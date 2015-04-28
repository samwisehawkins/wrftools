""" Script for running a WRF forecast and all of the pre-processsing, 
post-processing, visualization and verification which goes with it.

Config comes from a file, specified in an argument to the --config option.
Configuration can also be given at the command lind, and these will override
the configuration file. See example/forecast.yaml for an annotated list 
of options. 

Usage:
    run_forecast.py [--config=<file>] [options]
    
Options:
    --config=<file>
    --only=<stage>
    --delay=<hours>
    --bdy_conditions=<opt>
    --bdy_interval=<opt>
    --cmd_timing=<opt>
    --compression_level=<opt>
    --convert_grb=<opt>
    --cycles=<opt>
    --dispatch=<opt>
    --dispatch.list=<opt>
    --domain=<opt>
    --dry_run=<opt>
    --end=<opt>
    --extract=<opt>
    --extract.tseries=<opt>
    --extract_hgts=<opt>
    --fail_mode=<opt>
    --fcst_hours=<opt>
    --fetch=<opt>
    --fetch.gribmaster=<opt>
    --fetch.sst=<opt>
    --finalise=<opt>
    --finalise.copy=<opt>
    --finalise.create=<opt>
    --finalise.link=<opt>
    --finalise.move=<opt>
    --finalise.remove=<opt>
    --finalise.run=<opt>
    --full_trace=<opt>
    --geo_em_dir=<opt>
    --gm_dataset=<opt>
    --gm_dir=<opt>
    --gm_log=<opt>
    --gm_max_attempts=<opt>
    --gm_sleep=<opt>
    --gm_transfer=<opt>
    --grb_dir=<opt>
    --grb_fmt=<opt>
    --grb_input_delay=<opt>
    --grb_input_fmt=<opt>
    --history_interval=<opt>
    --host_file=<opt>
    --init_interval=<opt>
    --job_script=<opt>
    --job_template=<opt>
    --locations_file=<opt>
    --log.file=<opt>
    --log.fmt=<opt>
    --log.level=<opt>
    --log.mail=<opt>
    --log.mail.buffer=<opt>
    --log.mail.level=<opt>
    --log.mail.subject=<opt>
    --log.mail.to=<opt>
    --log.name=<opt>
    --max_dom=<opt>
    --max_job_time=<opt>
    --met_em_dir=<opt>
    --metadata=<opt>
    --model=<opt>
    --model_run=<opt>
    --namelist_input=<opt>
    --namelist_wps=<opt>
    --ncl_code=<opt>
    --ncl_code_dir=<opt>
    --ncl_log=<opt>
    --ncl_ol_code=<opt>
    --ncl_ol_out_dir=<opt>
    --ncl_opt_file=<opt>
    --ncl_opt_template=<opt>
    --ncl_out_dir=<opt>
    --ncl_out_type=<opt>
    --num_procs=<opt>
    --operational=<opt>
    --poll_interval=<opt>
    --post=<opt>
    --post.compress=<opt>
    --post.hyperslab=<opt>
    --post.hyperslab.dimspec=<opt>
    --post.met=<opt>
    --post.metadata=<opt>
    --post.upp=<opt>
    --prepare=<opt>
    --prepare.copy=<opt>
    --prepare.create=<opt>
    --prepare.link=<opt>
    --prepare.remove=<opt>
    --queue=<opt>
    --queue_log=<opt>
    --run_level=<opt>
    --simulate=<opt>
    --simulate.geogrid=<opt>
    --simulate.metgrid=<opt>
    --simulate.ndown=<opt>
    --simulate.real=<opt>
    --simulate.status=<opt>
    --simulate.timing=<opt>
    --simulate.ungrib=<opt>
    --simulate.wps=<opt>
    --simulate.wrf=<opt>
    --sst=<opt>
    --sst_delay=<opt>
    --sst_filename=<opt>
    --sst_local_dir=<opt>
    --sst_server=<opt>
    --sst_server_dir=<opt>
    --sst_vtable=<opt>
    --start=<opt>
    --status_file=<opt>
    --tmp_dir=<opt>
    --tseries_code=<opt>
    --tseries_dir=<opt>
    --tseries_file=<opt>
    --upp_dir=<opt>
    --visualise=<opt>
    --visualise.ncl=<opt>
    --visualise.ol=<opt>
    --vtable=<opt>
    --web_dir=<opt>
    --working_dir=<opt>
    --wps_dir=<opt>
    --wps_run_dir=<opt>
    --wrf_dir=<opt>
    --wrf_run_dir=<opt>
    --wrfout_dir=<opt>
    --wrftools_dir=<opt>
 
Any option which occurs in example/forecast.yaml can be supplied at the command-line, where it will take precedence.

A forecast is run in a series of stages
the main stages are: 

* fetch          - fetch boundary conditions
* prepare        - ensures correct files present, does some linking, updates namelist files
* simulate       - runs WPS and WRF
* post           - adds metadata, compresses files
* visualise      - calls NCL with specified scripts. Note the English (i.e. correct ;) spelling
* extract        - extracts time-series of variables at specified locations, relies on NCL
* finalise       - removes files, transfers locally, archive etc. 
* dispatch       - send out emails, plots etc

These are all available as boolean options e.g. `--fetch=false` will not run anything in the fetch stage.
Alternatively, individual stage(s) can be selected by passing it as an argument(s) to the `--only` option, e.g.
`--only=fetch`, will only run the fetch stage, even if other options contradict this. `--only=fetch,simulate` will 
run fetch and simulate stages."""


import sys
import time, datetime
from wrftools import confighelper as conf
import pprint
from wrftools import shared
from wrftools import prepare
from wrftools import fetch
from wrftools import simulate
from wrftools import visualise
from wrftools import post
from wrftools import extract
from wrftools import finalise

# these are the registered stages which can be turned on or off with config file and/or commad-line options
STAGES = ['fetch', 'prepare', 'simulate','post', 'visualise', 'extract', 'finalise', 'dispatch']

# Get configuration from command line and file, and merge the two
config = conf.config(__doc__, sys.argv[1:], flatten=True, format="yaml")

# horrible hack to ensure if start and end arguments 
# are supplied by the shell, they are parsed as datrtimes
if type(config['start'])==type(""):
    config['start'] = datetime.datetime.strptime(config['start'], '%Y-%m-%d_%H:%M:%S')
    config['end'] = datetime.datetime.strptime(config['end'], '%Y-%m-%d_%H:%M:%S')

# this allows a user to select only certain stages, and all others are set to false    
if config.get('only'): 
    config = shared.set_only_stages(config, STAGES)

        
#************************************************
# Logging
#************************************************
logger = shared.create_logger(config)

#************************************************
# Unpack some required settings
#************************************************
fcst_hours   = config['fcst_hours']               # forecast length
domain       = config['domain']                   # name of domain 
max_dom      = config['max_dom']                  # number of nests
fail_mode    = config['fail_mode']                # what to do on failure
full_trace   = config['full_trace']               # print a full stack trace
run_level    = config['run_level']


config['simulation.start'] = datetime.datetime.now()
#************************************************
# Print some information 
#************************************************
logger.info('*** FORECAST CYCLE STARTED ***')
for stage in STAGES:
    logger.info("    %s:    %s" %(stage.ljust(15), config[stage]))
logger.info('*****************************')


#**********************************************************
# Preparation of directories
#**********************************************************
try:
    prepare.prepare(config)
except Exception,e:
    shared.handle(e, fail_mode, full_trace)
    sys.exit()

    


    
#**********************************************************
# Forecast initial times
#**********************************************************
init_times = shared.get_init_times(config)

#**********************************************************
# Main outer loop of forecast cycle
#**********************************************************
logger.info('Running %d hour WRF forecasts for initial times from %s to %s' %(fcst_hours,init_times[0], init_times[-1]))

for init_time in init_times:
    #
    # Update the config state to reflect initial time
    #
    config['init_time'] = init_time
    logger.info('Running forecast from initial time: %s' %init_time) 

    #
    # Fetch
    #
    if config['fetch']:
        if config['fetch.gribmaster']:
            try:
                fetch.run_gribmaster(config)
            except IOError, e:
                logger.error('gribmaster failed for initial time %s' % init_time)
                shared.handle(e, fail_mode, full_trace)
        if config['sst']:
            fetch.get_sst(config)

            
            
    #
    # WPS
    #
    if config['simulate'] and config['simulate.wps']:

        try:
            simulate.update_namelist_wps(config)            
        except IOError, e:
            shared.handle(e, fail_mode, full_trace)


        if config['simulate.ungrib']:
            try:        
                simulate.run_ungrib(config)
            except Exception, e:
                shared.handle(e, fail_mode, full_trace)
        
        if config['simulate.ungrib'] and config['sst']:
            try:
                simulate.ungrib_sst(config)
            except Exception, e:
                shared.handle(e, fail_mode, full_trace)

        if config['simulate.geogrid']:
            try:
                simulate.run_geogrid(config)
            except Exception, e:
                shared.handle(e, fail_mode, full_trace)
        
        if config['simulate.metgrid']:
            try:
                simulate.run_metgrid(config)
            except Exception, e:
                shared.handle(e, fail_mode, full_trace)


   
    
    #
    # WRF standard preparation
    #           
    if config['simulate'] and config['simulate.wrf']:
        try:
            simulate.prepare_wrf(config)
            simulate.update_namelist_input(config)
        except Exception, e:
            shared.handle(e, fail_mode, full_trace)
        
        if config['simulate.real']:
            try:
                simulate.run_real(config)
            except Exception, e:
                shared.handle(e, fail_mode, full_trace)
    
    #
    # WRF runs
    #
    if config['simulate'] and config['simulate.wrf']:
        try:
            simulate.run_wrf(config)
        except Exception, e:
            shared.handle(e, fail_mode, full_trace)
        
        if config['simulate.timing']:
            try:
                simulate.timing(config)
            except Exception, e:
                shared.handle(e, fail_mode, full_trace)
        try:
           simulate.move_wrfout_files(config) # this will also copy namelists, logs etc
        except Exception, e:
            shared.handle(e, fail_mode, full_trace)
    
    # 
    if config['simulate'] and config['simulate.status']:
        logger.debug("writing status file")
        try:
            config['simulation.complete'] = datetime.datetime.now()
            shared.status(config)
        except Exception, e:
            logger.error('*** FAIL STATUS WRITE ***')
            shared.handle(e, fail_mode, full_trace)

    
    
        
    #
    # Visualisation
    #
    if config['visualise']:
        if config['visualise.ncl']:
            for d in range(1,max_dom+1):
                try:
                    logger.debug('Processing domain d%02d' %d)
                    config['dom'] = d
                    visualise.produce_ncl_plots(config)
                except Exception, e:
                    logger.error('*** FAIL VISUALISE ***')
                    shared.handle(e, fail_mode, full_trace)
    
        
        if config['visualise.ol']:
            for d in range(1,max_dom+1):
                try:
                    logger.debug('Processing domain d%02d' %d)
                    config['dom'] = d
                    visualise.produce_ncl_ol_plots(config)
                except Exception, e:
                    logger.error('*** FAIL NCL ***')
                    shared.handle(e, fail_mode, full_trace)
    
    
    #
    # Time series extraction
    #
    if config['extract'] and config['extract.tseries']:
        for d in range(1,max_dom+1):
            try:
                logger.debug('Processing domain d%02d' %d)
                config['dom'] = d
                config['grid_id'] = d
                extract.extract_tseries(config)
            except Exception, e:
                logger.error('*** FAIL NCL TIME SERIES ***')
                shared.handle(e, fail_mode, full_trace)

                
               
                
    #
    # Verification stage, not currenlty used
    # Point stat
    if config['post'] and config['post.met']:
        for d in range(1,max_dom+1):        
            try:
                config['dom'] = d
                post.run_point_stat(config)
            except Exception, e:
                shared.handle(e, fail_mode, full_trace)
    
            
    if config['dispatch']:
        from wrftools import dispatch
        dry_run = run_level=='DUMMY'
        dispatch.dispatch(config)

        
    #
    # Post processing - do this after visualisation
    #
    if config['post']:
        
        if config['post.hyperslab']:
            try:
                post.hyperslab(config)
            except Exception, e:
                shared.handle(e, fail_mode, full_trace)


        if config['post.compress']:
            try:
                post.compress(config)
            except Exception, e:
                shared.handle(e, fail_mode, full_trace)
        
        
        if config['post.metadata']:
            try:
                post.add_metadata(config)
            except Exception, e:
                shared.handle(e, fail_mode, full_trace)
   
    
        if config['post.upp']:
            for d in range(1,max_dom+1):
                try:
                    config['dom'] = d
                    post.run_unipost(config)
                except Exception, e:
                    logger.error('*** FAIL TIME SERIES ***')
                    shared.handle(e, fail_mode, full_trace)
                    
        
    if config['finalise']:
        logger.info('*** FINALISE ***')
        
        try:
            finalise.finalise(config)
        except Exception,e:
            logger.error('*** FAIL FINALISE ***')
            shared.handle(e, fail_mode, full_trace)

        
        

# Final code to get executed
logger.debug('Shutting down the logging framework')
shared.shutdown()
