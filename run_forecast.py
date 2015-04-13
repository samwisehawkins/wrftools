""" Script for running a WRF forecast and all of the pre-processsing, 
post-processing, visualization and verification which goes with it.

Config comes from a file, specified in an argument to the --config option.
Configuration can also be given at the command lind, and these will override
the configuration file. See example/forecast.yaml for an annotated list 
of options. 

Usage:
    run_forecast.py [--config=<file>] [options]

See examples/forecast.yaml for an annotated list of options. A forecast is run in a series of stages
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
run fetch and simulate stages.


Options:
    --archive_mode=<str>
    --bdy_conditions=<str>
    --bdy_interval=<int>
    --cmd_timing=<bool>
    --compress=<bool>
    --compression_level=<int>
    --config=<str>
    --convert_grb=<bool>
    --create_dirs=<list>
    --cycles=<str>
    --delay=<int>
    --dispatch=<bool>
    --dispatch_json=<str>
    --domain=<str>
    --dstd=<float>
    --end=<datetime.datetime>
    --extract=<bool>
    --extract.tseries=<bool>
    --extract_hgts=<str>
    --fail_mode=<str>
    --fcst_hours=<int>
    --fetch=<bool>
    --fetch.gribmaster=<bool>
    --fetch.sst=<bool>
    --finalise=<bool>
    --finalise.link=<list>
    --finalise.move=<list>
    --finalise.remove=<list>
    --full_trace=<bool>
    --geo_em_dir=<str>
    --gm_dataset=<str>
    --gm_delay=<int>
    --gm_dir=<str>
    --gm_log=<str>
    --gm_max_attempts=<int>
    --gm_sleep=<int>
    --gm_transfer=<str>
    --grb_dir=<str>
    --grb_fmt=<str>
    --grb_input_fmt=<str>
    --history_interval=<int>
    --host_file=<str>
    --init_interval=<int>
    --job_script=<str>
    --job_template=<str>
    --json_dir=<str>
    --json_web_dir=<str>
    --link=<list>
    --locations_file=<str>
    --log_file=<str>
    --log_fmt=<str>
    --log_level=<str>
    --mail_buffer=<int>
    --mail_level=<str>
    --mail_subject=<str>
    --mailto=<str>
    --max_dom=<int>
    --max_job_time=<dict>
    --met_em_dir=<str>
    --metadata=<bool>
    --model=<str>
    --model_run=<str>
    --namelist_input=<str>
    --namelist_wps=<str>
    --ncdump=<str>
    --ncl_code=<str>
    --ncl_code_dir=<str>
    --ncl_log=<str>
    --ncl_ol_code=<str>
    --ncl_ol_out_dir=<str>
    --ncl_ol_web_dir=<str>
    --ncl_opt_file=<str>
    --ncl_out_dir=<str>
    --ncl_out_type=<str>
    --ncl_web_dir=<str>
    --num_procs=<dict>
    --only=<string>
    --operational=<bool>
    --pcurve_dir=<str>
    --pdist=<int>
    --pnorm=<bool>
    --poll_interval=<dict>
    --post=<bool>
    --post.upp=<bool>
    --post.compress=<bool>
    --post.metadata=<bool>
    --post.hyperslab=<bool>
    --power=<bool>
    --power_file=<str>
    --pquants=<str>
    --pre_clean=<list>
    --prepare=<bool>
    --queue=<bool>
    --queue_name=<dict>
    --run_level=<str>
    --simulate=<bool>
    --simulate.geogrid=<bool>
    --simulate.metgrid=<bool>
    --simulate.ndown=<bool>
    --simulate.real=<bool>
    --simulate.status=<bool>
    --simulate.timing=<bool>
    --simulate.ungrib=<bool>
    --simulate.wps=<bool>
    --simulate.wrf=<bool>
    --sst=<bool>
    --sst_delay=<int>
    --sst_filename=<str>
    --sst_local_dir=<str>
    --sst_server=<str>
    --sst_server_dir=<str>
    --sst_vtable=<str>
    --sstd=<float>
    --start=<datetime.datetime>
    --status_file=<str>
    --tansfer.dispatch=<bool>
    --tmp_dir=<str>
    --transfer=<bool>
    --transfer.archive=<bool>
    --transfer_files=<list>
    --tseries_code=<str>
    --tseries_dir=<str>
    --tseries_fmt=<str>
    --upp_dir=<str>
    --visualise=<bool>
    --visualise.ol=<bool>
    --visualise.ncl=<bool>
    --vtable=<dict>
    --web_dir=<str>
    --working_dir=<str>
    --wps_dir=<str>
    --wps_run_dir=<str>
    --wrf_dir=<str>
    --wrf_run_dir=<str>
    --wrfout_dir=<str>
    --wrftools_dir=<str>"""


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
STAGES = ['fetch', 'prepare', 'simulate','post', 'visualise', 'extract', 'power', 'finalise', 'dispatch']

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

   
    
    #
    # Power prediction 
    #
    if config['power']:
        logger.warn("power forecaasing from within main forecast cycle is deprecated and will be removed")
        logger.warn("use power.py as a standalone tool, to preserve modularity")
        pass
        #
        #from wrftools import power
        #for d in range(1,max_dom+1):
        #    try:
        #        config['dom'] = d
        #        config['grid_id'] = d
        #        power.power(config)
        #    except Exception, e:
        #        logger.error('*** FAIL POWER CONVERSION ***')
        #        shared.handle(e, fail_mode, full_trace)


    # deprecated
    if config['extract'] and config['extract.tseries']:
        logger.warn("dumping time-series to other formats from within main forecast cycle is deprecated and will be removed")
        logger.warn("use ncdump.py as a standalone tool, to preserve modularity")
        pass
        #for d in range(1,max_dom+1):
        #    try:
        #        config['dom'] = d
        #        extract.ncdump(config)
        #    except Exception, e:
        #        logger.error('*** FAIL TIME SERIES DUMPING  ***')
        #        shared.handle(e, fail_mode, full_trace)


            
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
