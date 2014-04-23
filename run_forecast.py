""" Script for running a WRF forecast and all of the pre-processsing, 
post-processing, visualization and verification which goes with it.

Config comes from a file, specified in an argument to the --config option.
Configuation can also be given at the command lind, and these will override
the configuration file. See example/forecast.yaml for an annotated list 
of options. 

Usage:
    run_forecast.py [--config=<file>] [options]

See examples/forecast.yaml for an annotated list of options
    
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
    --operational=<bool>
    --pcurve_dir=<str>
    --pdist=<int>
    --pnorm=<bool>
    --poll_interval=<dict>
    --post=<bool>
    --post.upp=<bool>
    --post.compress=<bool>
    --post.metadata=<bool>
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
from wrftools import wrftools
import logging
from wrftools import confighelper as conf
import pprint

config = conf.config(__doc__, sys.argv[1:], flatten=True, format="yaml")
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(config)

#sys.exit()

#for key in sorted(config.keys()):
#    t = str(type(config[key]))
#    t = t.lstrip("'<type ").rstrip("'>")
#    print '%s=<%s>' % (key, t)


#************************************************
# Logging
#************************************************
logger = wrftools.create_logger(config)
    
    

#************************************************
# Get some required settings
#************************************************
fcst_hours   = config['fcst_hours']               # forecast length
domain       = config['domain']
max_dom      = config['max_dom']                  # number of nested domains
fail_mode    = config['fail_mode']                # what to do on failure



#************************************************
# Main options. Unpack from config to make sure 
# they are defined. Is this wise? What if an option 
# is not needed, why should it be defined?
#************************************************
logger.info('*** FORECAST CYCLE STARTED ***')
config['simulation_start'] = datetime.datetime.now()

run_level           = config['run_level']
fail_mode           = config['fail_mode']
full_trace          = config['full_trace']
fetch               = config['fetch']
gribmaster          = config['fetch.gribmaster']
convert_grb         = config['convert_grb']
sst                 = config['fetch.sst']
simulate            = config['simulate']
wps                 = config['simulate.wps']
ungrib              = config['simulate.ungrib']
geogrid             = config['simulate.geogrid']
metgrid             = config['simulate.metgrid']
ndown               = config['simulate.ndown']
real                = config['simulate.real']
wrf                 = config['simulate.wrf']
timing              = config['simulate.timing']
post                = config['post']
met                 = config['post.met']
compress            = config['post.compress']
metadata            = config['post.metadata']
upp                 = config['post.upp']
extract             = config['extract']
time_series         = config['extract.tseries']
power               = config['power']
visualise           = config['visualise']
dispatch            = config['dispatch']
finalise            = config['finalise']


#**********************************************************
# Preparation of directories
#**********************************************************
try:
    wrftools.prepare(config)
except Exception,e:
    wrftools.handle(e, fail_mode, full_trace)
    sys.exit()

#**********************************************************
# Forecast initial times
#**********************************************************
init_times = wrftools.get_init_times(config)

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
    if fetch:
        if gribmaster:
            try:
                wrftools.run_gribmaster(config)
            except IOError, e:
                logger.error('gribmaster failed for initial time %s' % init_time)
                wrftools.handle(e, fail_mode, full_trace)
        if sst:
            wrftools.get_sst(config)


            
            
    #
    # WPS
    #
    if simulate and wps:
        #try:
        #    wrftools.prepare_wps(config)
        #except IOError, e:
        #    logger.error('WPS failed for initial time %s' %init_time)
        #    wrftools.handle(e, fail_mode, full_trace)
        try:
            wrftools.update_namelist_wps(config)            
        except IOError, e:
            wrftools.handle(e, fail_mode, full_trace)


        if ungrib:
            try:        
                wrftools.run_ungrib(config)
            except Exception, e:
                wrftools.handle(e, fail_mode, full_trace)
        
        if sst:
            try:
                wrftools.ungrib_sst(config)
            except Exception, e:
                wrftools.handle(e, fail_mode, full_trace)

        if geogrid:
            try:
                wrftools.run_geogrid(config)
            except Exception, e:
                wrftools.handle(e, fail_mode, full_trace)
        
        if metgrid:
            try:
                wrftools.run_metgrid(config)
            except Exception, e:
                wrftools.handle(e, fail_mode, full_trace)


   
    
    #
    # WRF standard preparation
    #           
    if simulate and wrf and not ndown:
        try:
            wrftools.prepare_wrf(config)
            wrftools.update_namelist_input(config)
        except Exception, e:
            wrftools.handle(e, fail_mode, full_trace)
        
        if real:
            try:
                wrftools.run_real(config)
            except Exception, e:
                wrftools.handle(e, fail_mode, full_trace)
    
    #
    # WRF runs
    #
    if simulate and wrf:
        try:
            wrftools.run_wrf(config)
        except Exception, e:
            wrftools.handle(e, fail_mode, full_trace)
        
        if timing:
            try:
                wrftools.timing(config)
            except Exception, e:
                wrftools.handle(e, fail_mode, full_trace)
        try:
           wrftools.move_wrfout_files(config) # this will also copy namelists, logs etc
        except Exception, e:
            wrftools.handle(e, fail_mode, full_trace)
    
    
    if simulate and 'status' in config and config['status']:
        logger.debug("writing status file")
        try:
            config['simulation_complete'] = datetime.datetime.now()
            wrftools.status(config)
        except Exception, e:
            logger.error('*** FAIL STATUS WRITE ***')
            wrftools.handle(e, fail_mode, full_trace)

    
    
    #
    # Post processing
    #
    if post:
        if compress:
            try:
                wrftools.compress(config)
            except Exception, e:
                wrftools.handle(e, fail_mode, full_trace)

        
        if metadata:
            try:
                wrftools.add_metadata(config)
            except Exception, e:
                wrftools.handle(e, fail_mode, full_trace)
        
   
    
        if upp:
            for d in range(1,max_dom+1):
                try:
                    config['dom'] = d
                    wrftools.run_unipost(config)
                except Exception, e:
                    logger.error('*** FAIL TIME SERIES ***')
                    wrftools.handle(e, fail_mode, full_trace)
                    
        if convert_grb:
            for d in range(1,max_dom+1):
                try:
                    config['dom'] = d
                    wrftools.convert_grib(config)
                except Exception, e:
                    logger.error('*** FAIL GRIB CONVERSION ***')
                    wrftools.handle(e, fail_mode, full_trace)


                
                
    #
    # Met verification tools
    #
    if met:
        for d in range(1,max_dom+1):        
            try:
                config['dom'] = d
                wrftools.run_point_stat(config)
            except Exception, e:
                wrftools.handle(e, fail_mode, full_trace)

        
    #
    # Visualisation
    #
    if visualise:
        if config['visualise.ncl']:
            for d in range(1,max_dom+1):
                try:
                    logger.debug('Processing domain d%02d' %d)
                    config['dom'] = d
                    wrftools.produce_ncl_plots(config)
                except Exception, e:
                    logger.error('*** FAIL VISUALISE ***')
                    wrftools.handle(e, fail_mode, full_trace)
    
        
        if config['visualise.ol']:
            for d in range(1,max_dom+1):
                try:
                    logger.debug('Processing domain d%02d' %d)
                    config['dom'] = d
                    wrftools.produce_ncl_ol_plots(config)
                except Exception, e:
                    logger.error('*** FAIL NCL ***')
                    wrftools.handle(e, fail_mode, full_trace)
    
    if extract and time_series:
        for d in range(1,max_dom+1):
            try:
                logger.debug('Processing domain d%02d' %d)
                config['dom'] = d
                config['grid_id'] = d
                wrftools.extract_tseries(config)
            except Exception, e:
                logger.error('*** FAIL NCL TIME SERIES ***')
                wrftools.handle(e, fail_mode, full_trace)

                
    #
    # Some bug seems to be creeping in, causing the programme to 
    # fail silently around here. I'm adding a sleep statement
    # as I have a hunch this might be some kind of race condition
    #
    #logger.warn('*** SLEEPING FOR 1 SECONDS TO ENSURE TSERIES FILES ARE CLOSED ***')
    #time.sleep(1)

    
    
    
    if power:
        for d in range(1,max_dom+1):
            try:
                config['dom'] = d
                config['grid_id'] = d
                wrftools.power(config)
            except Exception, e:
                logger.error('*** FAIL POWER CONVERSION ***')
                wrftools.handle(e, fail_mode, full_trace)


    if extract and time_series:
        for d in range(1,max_dom+1):
            try:
                config['dom'] = d
                wrftools.ncdump(config)
            except Exception, e:
                logger.error('*** FAIL TIME SERIES DUMPING  ***')
                wrftools.handle(e, fail_mode, full_trace)

    if finalise:
        logger.info('*** FINALISE ***')
        
        try:
            wrftools.finalise(config)
        except Exception,e:
            logger.error('*** FAIL FINALISE ***')
            wrftools.handle(e, fail_mode, full_trace)

            
    if dispatch:
        dry_run = run_level=='DUMMY'
        wrftools.dispatch(config)



# Final code to get executed
logger.debug('Shutting down the logging framework')
logging.shutdown()
