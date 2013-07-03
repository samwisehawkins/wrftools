#!/usr/bin/env python

#*************************************************************
# Top-level script for running a WRF forecast and all of 
# the pre-processsing, post-processing, visualization
# and verification which goes with it.
#
# This can be run as a command-line script where the first
# argument MUST BE a configuration file which sets most 
# of the options.  These options can be overridden by speciying
# further arguments in the form: --key=value. 
#
# The philosophy is to keep this script as simple and clean 
# as possible to represent the high-level progamme flow. 
# Each stage in the process should try and follow the same 
# loop structure.
#
# All of the heavy lifting is done in the wrftools
# module. This script this ties it all together, initialises 
# the logging framework and does some basic error checking.  
#
# A (questionable) design choice is to use a configuration file 
# with the same (at least similar)
# syntax to the namelist.wps and namelist.input files used by WRF
# so that the same code can be re-used reading these.
#
# AUTHOR: sam.hawkins@vattenfall.com
#**************************************************************

import sys
import time, datetime
import wrftools
import logging

nl      = wrftools.read_namelist(sys.argv[1])
config  = nl.settings

#
# Allow command-line arguments to override those in the namelist file
# no checking is done here, we just merrily assume the arguments 
# are given in the correct order. They should be specified like this
#
# --option=value 
#
if len(sys.argv)>2:
    cmd_args = sys.argv[2:]
    wrftools.add_cmd_args(config, cmd_args)

#
# Get some required settings
#
fcst_hours   = config['fcst_hours']               # forecast length
base_dir     = config['base_dir']
domain       = config['domain']
max_dom      = config['max_dom']                  # number of nested domains
fail_mode    = config['fail_mode']                # what to do on failure


#************************************************
# Logging
#************************************************
logger = wrftools.create_logger(config)

#for key in config.keys():
#    logger.debug('%s: %s' %(key, config[key]))

#***********************************************
# Initial checks
#***********************************************
try:
    wrftools.check_config(config)
except KeyError:
    logger.error('required setting missing')
    sys.exit()



#************************************************
# Main options. Unpack from config to make sure 
# they are defined
#************************************************
logger.info('*** FORECAST CYCLE STARTED ***')
fail_mode           = config['fail_mode']
full_trace          = config['full_trace']
gribmaster          = config['gribmaster']
sst                 = config['sst']
wps                 = config['wps']
wrf                 = config['wrf']
upp                 = config['upp']
time_series         = config['time_series']
json                = config['json']
power               = config['power']
ncl                 = config['ncl']
scripts             = config['scripts']
met                 = config['met']
convert_grb         = config['convert_grb']
timing              = config['timing'] # produce timing information
web                 = config['web']
archive             = config['archive']
summarise           = config['summarise']
cleanup             = config['cleanup']


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
    # Gribmaster
    #
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
    # bit of a hack calling prepare_wps twice, but need to re-link things after 
    # running for SST
    #
    if wps:
        try:
            wrftools.prepare_wps(config)
            wrftools.update_namelist_wps(config)
            wrftools.run_ungrib(config)
            if sst:
                wrftools.ungrib_sst(config)
            wrftools.run_geogrid(config)
            wrftools.run_metgrid(config)
        except IOError, e:
            logger.error('WPS failed for initial time %s' %init_time)
            wrftools.handle(e, fail_mode, full_trace)
    #
    # WRF
    #           
    if wrf:
        try:
            wrftools.prepare_wrf(config)
        except Exception, e:
            wrftools.handle(e, fail_mode, full_trace)
        try:
            wrftools.update_namelist_input(config)
        except Exception, e:
            wrftools.handle(e, fail_mode, full_trace)
        try:
            wrftools.run_real(config)
        except Exception, e:
            wrftools.handle(e, fail_mode, full_trace)
        try:
            wrftools.run_wrf(config)
            #pass
        except Exception, e:
            wrftools.handle(e, fail_mode, full_trace)
        try:
           wrftools.move_wrfout_files(config) # this will also copy namelists, logs etc
        except Exception, e:
            wrftools.handle(e, fail_mode, full_trace)
    
    logger.warn('*** SLEEPING FOR 10 SECONDS TO ALLOW FS TIME TO SORT ITSELF OUT ***')
    time.sleep(10)
    
    #
    # Computing time
    #
    if timing:
        try:
            wrftools.timing(config)
        except Exception, e:
            logger.error('*** FAIL TIMING ***')
            wrftools.handle(e, fail_mode, full_trace)
    #
    # Post processing
    #
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
    if power:
        for d in range(1,max_dom+1):
            try:
                config['dom'] = d
                wrftools.power(config)
            except Exception, e:
                logger.error('*** FAIL POWER CONVERSION ***')
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
    if ncl:
        for d in range(1,max_dom+1):
            try:
                logger.debug('Processing domain d%02d' %d)
                config['dom'] = d
                wrftools.produce_ncl_plots(config)
            except Exception, e:
                logger.error('*** FAIL NCL ***')
                wrftools.handle(e, fail_mode, full_trace)
    
        if web:
            wrftools.transfer_to_web_dir(config)

    #
    # Extract time-series from grib files
    #
    if time_series:
        for d in range(1,max_dom+1):
            try:
                config['dom'] = d
                wrftools.extract_tseries(config)
            except Exception, e:
                logger.error('*** FAIL TIME SERIES ***')
                wrftools.handle(e, fail_mode, full_trace)

    #
    # Some bug seems to be creeping in, causing the programme to 
    # fail silently around here. I'm adding a sleep statement
    # as I have a hunch this might be some kind of race condition
    #
    logger.warn('*** SLEEPING FOR 10 SECONDS TO ENSURE TSERIES FILES ARE CLOSED ***')
    time.sleep(10)

    if json:
        try:
            wrftools.tseries_to_json(config)
        except Exception, e:
                logger.error('*** FAIL JSON CONVERSION ***')
                wrftools.handle(e, fail_mode, full_trace)

        if web:
            logger.info('*** TRANSFERRING JSON TO WEB DIR ***')
            try:
                wrftools.json_to_web(config)
            except Exception,e:
                logger.error('*** FAIL TRANSFERRING JSON ***')
                wrftools.handle(e, fail_mode, full_trace)
    #
    # Any additional scripts
    #
    if scripts:
        try:
            wrftools.run_scripts(config)
        except Exception, e:
            logger.error('*** FAIL ADDITONAL SCRIPTS ***')
            wrftools.handle(e, fail_mode, full_trace)


    if archive:
        logger.debug("moving files to longbackup")
        wrftools.archive(config)

    if cleanup:
        logger.debug("cleaning up files")
        wrftools.cleanup(config)

    if summarise:
        wrftools.summarise(config)


# Final code to get executed
logger.debug('Shutting down the logging framework')
logging.shutdown()
