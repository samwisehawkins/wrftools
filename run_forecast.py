#!/usr/bin/env python

#*************************************************************
# Top-level script for running a WRF forecast and all of 
# the pre-processsing, post-processing, visualization
# and verification which goes with it.
#
# This can be run as a command-line script where the first
# and only argument is a configuration file which sets most 
# of the options.
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
# Another design choice is to have output files archived by initial 
# time, so that subsequent visualisation and verification can 
# be done using the same outer-loop as this script. 
#
#
# A further  design choice is to use a configuration file 
# with the same (at least similar)
# syntax to the namelist.wps and namelist.input files used by WRF
# so that the same code can be re-used reading these.
#
# TODO: get rid of outer case loop. This is unecessary, if we
#       just generalise the code so that start and end can be lists
#       and get_init_times et al return init_times which are not 
#       necessarily contiguous. We want to get rid of test_case in 
#       the meta-data since it is extraneous, as it is already defined 
#       by the init_time. 
#
#       tidy up logging statements so they are consistent
#       add performance/timing code - 
#       add visualisation codes - DONE
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
# Get some required settings
#
fcst_hours   = config['fcst_hours']               # forecast length
base_dir     = config['base_dir']
domain       = config['domain']
domain_dir   = '%s/%s' % (base_dir, domain)
config['domain_dir'] = domain_dir                 # domain directory
max_dom      = config['max_dom']                  # number of nested domains
fail_mode    = config['fail_mode']                # what to do on failure


#***********************************************
# Initial checks
#***********************************************
try:
    wrftools.check_config(config)
except KeyError:
    logger.error('required setting missing')
    sys.exit()

#************************************************
# Logging
#************************************************
logger = wrftools.create_logger(config)


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
                wrftools.transfer_to_web_dir(config)
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
                wrftools.tseries_to_json(config)

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
