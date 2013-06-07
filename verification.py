#!/usr/bin/env python

import sys
import time, datetime
import wrftools

config       = wrftools.read_namelist(sys.argv[1]).settings


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
logger.info('*** FORECAST CYCLE STARTED ***')


#************************************************
# Main options
#************************************************
gribmaster          = config['gribmaster']
sst                 = config['sst']
wps                 = config['wps']
wrf                 = config['wrf']
upp                 = config['upp']
time_series         = config['time_series']
power               = config['power']
ncl                 = config['ncl']
jesper              = config['jesper']
met                 = config['met']
convert_grb         = config['convert_grb']
timing              = config['timing'] # produce timing information
archive             = config['archive']
cleanup             = config['cleanup']


for model_run in ['ABA']:
    config['model_run'] = model_run
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
        # Met verification tools
        #
        config['init_time'] = init_time
        for d in range(1,max_dom+1):        
            try:
                config['dom'] = d
                wrftools.run_point_stat(config)
            except:
                wrftools.handle(config)

