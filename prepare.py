""" Script for preparing directories and files for WRF simulation. This creates a seperate directory 
for each WRF simulation e.g. each initialsation time. These simulation directories are self-contained, 
with all inputs, outputs, and excutables either copied or linked into them.  
This enables job-level parallelisation when running large reanalysis or reforecasting cases.

Config comes from a file, specified as --config argument. Some configuration options (listed below) 
can also be given at the command line, where they will override the configuration file. 
See example/forecast.yaml for a full list of configuration options. 

Usage:
    prepare.py [--config=<file>] [options]
    
Options:
    --config=<file>         yaml/json file specificying any of the options below
    --start=<time>          an initial time to start simulation from, if not specified, a time will be derived from base-time, delay and cycles 
    --base-time=<time>
    --delay=<hours>         number of hours delay to apply to start time
    --cycles=<hours>        list of hours to restrict start times to e.g. [0,12]
    --end=<time>            an end time for the simulation blocks
    --init-interval=<hours> number of hours between initialistions
    --working_dir=<dir>     working directory specifier which may contain date and time placeholders, see below
    --wps-dir=<dir>         base directory of the WPS installation
    --wrf-dir=<dir>         base directory of the WRF installation
    --namelist-wps=<file>   location of namelist.wps template to use, a modified copy will be placed into working_dir
    --namelist-input=<file> location of namelist.input template to use, a modified copy will be places into working_dir
    --link-boundaries=<bool> try to expand ungrib sections and link in appropriate boundary conditions
    --rmtree                remove working directory tree first - use with caution!
    --dry-run               log but don't execute commands
    --log.level=<level>     log level info, debug or warn (see python logging modules)
    --log.format=<fmt>      log format code (see python logging module)
    --log.file=<file>       optional log file"""

LOGGER="wrftools"

import sys
import os
import shutil
import subprocess
import glob
import datetime
import collections
from dateutil import rrule
from wrftools import namelist
from wrftools import substitute
from wrftools import templater
import confighelper as conf
import loghelper
from wrftools import shared


class UnsafeDeletion(Exception):
    """Exception rasied when code looks like it may cause an usafe deletion"""
    pass


        
def main():

    # merge command-line and file-specified arguments
    config = conf.config(__doc__, sys.argv[1:])





    logger = loghelper.create(LOGGER, log_level=config.get('log.level'), 
                              log_fmt=config.get('log.format'), 
                              log_file=config.get('log.file'))
    
    
    if not os.path.exists(config['namelist_wps']):
        logger.error("No namelist.input found, %s was specifed as template, but does not exist" % config['namelist_wps'])
        sys.exit()
    
    if not os.path.exists(config['namelist_input']):
        logger.error("No namelist.input found, %s was specifed as template, but does not exist" % config['namlist_input'])
        sys.exit()
    
    
    
    # either the start time is exactly specified, or else we calculate it
    if config.get('start'):
        init_time = config['start']
    else:
        init_time = shared.get_time(base_time=config.get('base-time'), delay=config.get('delay'), round=config.get('cycles'))

    if config.get('end'):
        end_init = config['end']
        logger.debug(end_init)
        init_interval = config['init_interval']
        init_times = list(rrule.rrule(freq=rrule.HOURLY, interval=init_interval, dtstart=init_time, until=end_init))
    else:
        init_times = [init_time]



    for init_time in init_times:
        try:

            prepare(config, init_time)
        
        except IOError as e:
            logger.error(e)

            
def prepare(config, init_time):
    
    logger = loghelper.get(LOGGER)
    
    logger.info("**** Running simulation for %s *****" % init_time)
    
    dry_run = config.get('dry-run')
    rmtree = config.get('rmtree')
    max_dom = config['max_dom']
    bdy_interval = config['bdy_interval']
    fcst_hours = config['fcst_hours']
    

    history_interval = config['history_interval'] 
    link_boundaries = config.get('link-boundaries')

    
    
    # one-argument function to do initial-time substitution in strings
    expand = lambda s : substitute.sub_date(s, init_time=init_time) if type(s)==type("") else s

    date_replacements = substitute.date_replacements(init_time=init_time)
    
    working_dir = expand(config['working_dir'])
    logger.info("working dir: %s " % working_dir)

    if rmtree:
        safe_remove(working_dir, dry_run)
    
    create_directory_structure(expand, remove=config.get('prepare.remove'), create=config.get('prepare.create'), copy=config.get('prepare.copy'), link=config.get('prepare.link'), dry_run=dry_run)    
    
    if config.get('prepare.template'):
        for entry in config['prepare.template']:
            tokens = expand(entry).split()
            source = tokens[0]
            target = tokens[1] if len(tokens)>1 else tokens[0]
            templater.fill_template(source, target, date_replacements)


    
    bdy_times = shared.get_bdy_times(init_time, fcst_hours, bdy_interval)
    
    working_namelist = working_dir+"/namelist.wps"

    # this can be made cleaner
    prefix=''
    update_namelist_wps(config['namelist_wps'], working_namelist, config['max_dom'], 
                        init_time, fcst_hours, config['bdy_interval'], 
                        config['geo_em_dir'], config['met_em_dir'], config['geogrid_run_dir'], config['metgrid_run_dir'], prefix, 
                        config.get('constants_name'))

    working_namelist = working_dir+"/namelist.input"
    logger.debug(fcst_hours)
    
    update_namelist_input(config['namelist_input'], working_namelist, max_dom, init_time, fcst_hours, history_interval, bdy_interval*60*60, metadata=config.get('metadata'))    

    
    # apply any additional specified namelist updates (consider getting rid of this section)
    namelist_updates = config.get('namelist_updates')
    if namelist_updates:
        for key in sorted(namelist_updates.keys()):
            entry = namelist_updates[key]
            logger.debug('processing namelist update entry %s' % key)
            
            template = expand(entry['template'])
            target = expand(entry['target'])
            logger.debug('%s\t---->\t%s' %(template.ljust(20), target.ljust(20)))
            namelist = shared.read_namelist(template)
            if entry.get('update'):
                for old,new in entry['update'].items():
                    logger.debug('\t%s\t:\t%s' %(old.ljust(20), expand(new).ljust(20)))
                    namelist.update(old,expand(new))
            namelist.to_file(target)



    # link in input files for all ungrib jobs
    # update namelist.wps to modify start and end time
    
    if config.get('ungrib'):
        for key,entry in config['ungrib'].items():
            # apply any delay and rounding to the init_time to get correct time for dataset
            # note that sometimes it is necessary to use a different time e.g. for SST field is delayed by one day
            run_dir = expand(entry['run_dir'])
            base_time = shared.get_time(init_time, delay=entry.get('delay'), round=entry.get('cycles'))
            ungrib_len = int(entry['ungrib_len'])
            bdy_times = shared.get_bdy_times(base_time, ungrib_len, bdy_interval)
            namelist = shared.read_namelist(run_dir+"/namelist.wps")

            start_str  = base_time.strftime("%Y-%m-%d_%H:%M:%S")
            end_str    = bdy_times[-1].strftime("%Y-%m-%d_%H:%M:%S")

            namelist.update('start_date', [start_str]*max_dom)
            namelist.update('end_date',   [end_str]*max_dom)
            namelist.to_file(run_dir+"/namelist.wps")
            
            # link in vtable
            vtable = entry['vtable']
            cmd = "%s %s/Vtable" % (vtable, run_dir)
            shared.link(cmd, dry_run=dry_run)
       

            if link_boundaries:
       
                file_pattern = entry['files']
                
                # create an ordered set to ensure filenames only appear once
                filenames = shared.ordered_set([substitute.sub_date(file_pattern, init_time=base_time, valid_time=t) for t in bdy_times])
                missing_files = []
                for f in filenames:
                    if not os.path.exists(f): 
                        missing_files.append(f)
                        logger.error("%s \t missing" % f)
                        
                if missing_files!=[]:
                    if config.get('missing_files'):
                        with open(config['missing_files'], "a") as f:
                            f.write(str(init_time)+"\n")
                    if rmtree:
                        safe_remove(working_dir, dry_run)

                    raise IOError("some files could not be found")


                args = ' '.join(filenames)
                cmd = '%s/link_grib.csh %s' %(run_dir,args)
                shared.run_cmd(cmd, dry_run=dry_run, cwd=run_dir, log=False)            
    
        
def update_namelist_input(template, target, max_dom, init_time, fcst_hours, history_interval, interval_seconds, metadata=None):    
    """ Updates the namelist.input file to reflect updated settings in config.
    Adds a non-standard &metadata section to give a name to the model run
    
    Arguments:
    config -- dictionary containing various configuration options
        
    """        
    logger =shared.get_logger()        
    logger.debug('*** UPDATING namelist.input ***')
    logger.debug(target)
    logger.debug(fcst_hours)
    namelist        = shared.read_namelist(template)   


    
    if metadata:
        for key,value in metadata.items():
            namelist.update(key, value, section='metadata')

    
    fcst_times = shared.get_interval_times(start=init_time, count=fcst_hours+1, freq=rrule.HOURLY)
    
    
    start   = fcst_times[0]
    end     = fcst_times[-1]
       
    #
    # I'm still not sure how the WRF namelist works between 
    # the start and end settings and the run_XX settings.
    # I think we can just keep days as zero, and work entirely
    # in hours
    #
    namelist.update('start_year', [start.year] * max_dom)
    namelist.update('start_month',[start.month]* max_dom)
    namelist.update('start_day',  [start.day]  * max_dom)
    namelist.update('start_hour', [start.hour] * max_dom)
    namelist.update('end_year',   [end.year]   * max_dom)
    namelist.update('end_month',  [end.month]  * max_dom)
    namelist.update('end_day',    [end.day]    * max_dom)
    namelist.update('end_hour',   [end.hour]   * max_dom)
    namelist.update('run_days',   [0])   
    namelist.update('run_hours',  [fcst_hours] )   
    #namelist.update('run_minutes',[0])   
    namelist.update('history_interval', [history_interval] * max_dom)
    namelist.update('interval_seconds', [interval_seconds])


    #
    # If DFI is being used, update DFI settings
    # From user guide:
    # "For time specification, it typically needs to integrate 
    # backward for 0.5 to 1 hour, and integrate forward for half of the time."
    #
    # should we just write this everytime into the file and rely of dfi_opt 
    # as the on/off switch?
    #
    hour         = datetime.timedelta(0, 60*60)
    minute       = datetime.timedelta(0, 60)
    #dfi_bck      = config['dfi_bck'] * minute
    #dfi_fwd      = config['dfi_fwd'] * minute
    #dfi_bckstop  = start - dfi_bck
    #dfi_fwdstop  = start + dfi_fwd
    

    #namelist.update('dfi_bckstop_year',   dfi_bckstop.year,   'dfi_control')
    #namelist.update('dfi_bckstop_month',  dfi_bckstop.month,  'dfi_control')
    #namelist.update('dfi_bckstop_day',    dfi_bckstop.day,    'dfi_control')
    #namelist.update('dfi_bckstop_hour',   dfi_bckstop.hour,   'dfi_control')
    #namelist.update('dfi_bckstop_minute', dfi_bckstop.minute, 'dfi_control')
    #namelist.update('dfi_bckstop_second', dfi_bckstop.second, 'dfi_control')
    #namelist.update('dfi_fwdstop_year',   dfi_fwdstop.year,   'dfi_control')
    #namelist.update('dfi_fwdstop_month',  dfi_fwdstop.month,  'dfi_control')
    #namelist.update('dfi_fwdstop_day',    dfi_fwdstop.day,    'dfi_control')
    #namelist.update('dfi_fwdstop_hour',   dfi_fwdstop.hour,   'dfi_control')
    #namelist.update('dfi_fwdstop_minute', dfi_fwdstop.minute, 'dfi_control')
    #namelist.update('dfi_fwdstop_second', dfi_fwdstop.second, 'dfi_control')
   
    namelist.to_file(target)

    logger.debug('*** FINISHED UPDATING namelist.input ***')          
        
        
def update_namelist_wps(template, target, max_dom, init_time, fcst_hours, bdy_interval, geo_em_dir, met_em_dir, geogrid_tbl, metgrid_tbl, prefix, constants_name=None):
    """ Updates the namelist.wps to reflect updated settings in config
    
    Arguments:
        expand -- function for exanding any strings
        template -- base namelist_wps file to alter 
        target  -- name of modified file to write to
        
    """    
    # consider refactoring this method, perhaps relacing it with a more general namelist updating function,
    # and pushing some of the logic into the configuration file?
    logger     = shared.get_logger()
    logger.debug('*** UPDATING namelist.wps ***')

    # function to expand any date/time placeholders
    expand = lambda s : substitute.sub_date(s, init_time=init_time)
    
    #wps_run_dir= expand(target)
    
    bdy_times  = shared.get_bdy_times(init_time, fcst_hours, bdy_interval)

    met_em_dir = expand(met_em_dir)
    geo_em_dir = expand(geo_em_dir)

    interval_seconds = bdy_interval * 60 * 60

    logger.debug('reading namelist.wps <--------- %s' % template)
    namelist = shared.read_namelist(template)

    #
    # Update some options based on the forecast config file
    #
    namelist.update('max_dom', max_dom)
    namelist.update('opt_output_from_geogrid_path', geo_em_dir, section='share')
    namelist.update('opt_output_from_metgrid_path', met_em_dir, section='metgrid')
    namelist.update('opt_geogrid_tbl_path', expand(geogrid_tbl), section='geogrid')
    namelist.update('opt_metgrid_tbl_path', expand(metgrid_tbl), section='metgrid')
    namelist.update('interval_seconds', [interval_seconds])
    
    #
    # Generate formatted strings for inclusion in the namelist.wps file
    #
    start_str  = bdy_times[0].strftime("%Y-%m-%d_%H:%M:%S")
    end_str    = bdy_times[-1].strftime("%Y-%m-%d_%H:%M:%S")
    logger.debug("Updating namelist.wps start and end")

    namelist.update('start_date', [start_str]*max_dom)
    namelist.update('end_date',   [end_str]*max_dom)

    if constants_name:
        namelist.update('constants_name', constants_name, section='metgrid')
    
    namelist.to_file(target)
    logger.debug('*** FINISHED UPDATING namelist.wps ***')
        
    
def create_directory_structure(expand, remove=None, create=None,copy=None,link=None, dry_run=False):
    """Creates a subdirectory structure, and copies, moves, and links in files
    
    Arguments:
        expand  -- a single-argument function to perform any string substitutions on any of the input arguments
        create  -- a list of subdirectories to create if they don't already exists
        remove  -- a list of file patterns to remove
        copy    -- a list of file patterns to copy
        link    -- a list of file patterns to link
        dry_run -- log rather than execute commands 

    """        
    # pass initial time as an argument, to leave a one-argument function which will expand strings

    logger = loghelper.get(LOGGER)
    if create:
        for d in create:
            subdir = expand(d)
            shared.create(subdir, dry_run=dry_run)

    if remove:
        for pattern in remove:
            shared.remove(expand(pattern), dry_run=dry_run)

    if copy:
        for pattern in copy:
            shared.copy(expand(pattern), dry_run=dry_run)
            
    if link:
        for pattern in link:
            shared.link(expand(pattern), dry_run=dry_run)

        
def safe_remove(path, dry_run=False):
    
    logger = loghelper.get(LOGGER)
    
    # try and prevent removing someting unsafe: root path, unexpanded wildcards, or paths which are just too short
    cnd1 = path == "/" 
    cnd2 = "*" in path
    cnd3 = len(path.split("/"))<3
    
    if cnd1 or cnd2 or cnd3:
        raise UnsafeDeletion("Unsafe deletion detected with path %s") % path
    
    logger.warn("removing path %s" % path)
    if not dry_run and os.path.exists(path):
        shutil.rmtree(path)        


def generate_replacements(mapping, template_expr, expander):
    expand_key = lambda s : template_expr % s
    
    replacements = { expand_key(key) : expander(value) for (key,value) in mapping.items()}
    return replacements


        
if '__main__' in __name__:
    main()
