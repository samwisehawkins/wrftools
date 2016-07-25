""" Script for checking existince of boundary condition files for WRF simulation. 

Config comes from a file, specified as --config argument. Some configuration options (listed below) 
can also be given at the command line, where they will override the configuration file. 
See example/forecast.yaml for a full list of configuration options. 

Usage:
    check.py [--config=<file>] [options]
    
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
        logger.error("No namelist.wps found, %s was specifed as template, but does not exist" % config['namelist_wps'])
        sys.exit()
    
    if not os.path.exists(config['namelist_input']):
        logger.error("No namelist.input found, %s was specifed as template, but does not exist" % config['namlist_input'])
        sys.exit()
    
    ok_files = config.get('ok_files')
    
    # dates with missing boundary conditions
    missing_files = config.get('missing_files')
    
    if ok_files is not None and os.path.exists(ok_files):
        os.remove(ok_files)

    if missing_files is not None and os.path.exists(missing_files):
        os.remove(missing_files)
    
    ok_file = open(ok_files, 'a')
    init_file = config.get('init_times')
    lines = open(init_file, 'r').readlines()
    for l in lines:
        date_token = l.strip('\n')
        init_time = datetime.datetime.strptime(date_token, "%Y-%m-%d %H:%M:%S")
        ok = check(config, init_time)
        if ok==True:
            ok_file.write(l)
            
    ok_file.close()
    
def check(config, init_time):
    
    logger = loghelper.get(LOGGER)
    
    logger.info("checking %s " % init_time)
    

    bdy_interval = config['bdy_interval']
    fcst_hours = config['fcst_hours']
    
    
    # one-argument function to do initial-time substitution in strings
    expand = lambda s : substitute.sub_date(s, init_time=init_time) if type(s)==type("") else s

    date_replacements = substitute.date_replacements(init_time=init_time)
    
    working_dir = expand(config['working_dir'])
    
    bdy_times = shared.get_bdy_times(init_time, fcst_hours, bdy_interval)
    
        
    
    # link in input files for all ungrib jobs
    # update namelist.wps to modify start and end time
    

    missing_files = []
    for key,entry in config['ungrib'].items():
        # apply any delay and rounding to the init_time to get correct time for dataset
        # note that sometimes it is necessary to use a different time e.g. for SST field is delayed by one day

        base_time = shared.get_time(init_time, delay=entry.get('delay'), round=entry.get('cycles'))
        ungrib_len = int(entry['ungrib_len'])
        bdy_times = shared.get_bdy_times(base_time, ungrib_len, bdy_interval)

        start_str  = base_time.strftime("%Y-%m-%d_%H:%M:%S")
        end_str    = bdy_times[-1].strftime("%Y-%m-%d_%H:%M:%S")
   
        file_pattern = entry['files']
        
        # create an ordered set to ensure filenames only appear once
        filenames = shared.ordered_set([substitute.sub_date(file_pattern, init_time=base_time, valid_time=t) for t in bdy_times])

        for f in filenames:
            if not os.path.exists(f): 
                missing_files.append(f)
                logger.error("%s \t missing" % f)

    all_ok = missing_files==[]
                
    if not all_ok:

        if config.get('missing_files'):
            with open(config['missing_files'], "a") as f:
                f.write(str(init_time)+"\n\t")
                f.write("\n\t".join(missing_files))
                f.write("\n")
    else:
        if config.get('ok_files'):
            with open(config['ok_files'], "a") as f:
                f.write("%s\n" % init_time.strftime("%Y-%m-%d_%H:%M:%S"))

    

    if all_ok:
        logger.info("\t ok") 
    
    return all_ok



        
if '__main__' in __name__:
    main()
