""" Script for checking existince of boundary condition files for WRF simulation. 

Config comes from a file, specified as --config argument. 
Usage:
    check.py --config=<file> [--log-level=<level>] [--log-format=<fmt>] [--log-file=<file>] <times>
    
Options:
    --config=<file>         yaml file specifying full options 
    --log-level=<level>     log level info, debug or warn (see python logging modules)
    --log-format=<fmt>      log format code (see python logging module)
    --log-file=<file>       optional log file
    <times>                 either single init times, or file with one per line"""

LOGGER="wrftools"

import sys
import os
import confighelper as conf
import loghelper
from wrftools import shared
from wrftools import substitute

class UnsafeDeletion(Exception):
    """Exception rasied when code looks like it may cause an usafe deletion"""
    pass


        
def main():

    # merge command-line and file-specified arguments
    config = conf.config(__doc__, sys.argv[1:])

    logger = loghelper.create(LOGGER, log_level=config.get('log-level'), 
                              log_fmt=config.get('log-format'), 
                              log_file=config.get('log-file'))
    
    
    init_times = shared.read_times(config['<times>'])
    
    ok_files = open(config['ok_files'], 'w')
    missing_files = open(config['missing_files'], 'w')
    
    # check that the namelist files exist
    if not os.path.exists(config['namelist_wps']):
        msg = "No namelist.wps found, %s was specifed as template, but does not exist" % config['namelist_wps']
        logger.error(msg)
        raise IOError(msg)
    
    if not os.path.exists(config['namelist_input']):
        msg = "No namelist.wps found, %s was specifed as template, but does not exist" % config['namelist_wps']
        logger.error(msg)
        raise IOError(msg)
    
    for init_time in init_times:
        missing = check(config, init_time)
        if missing==[]:
            ok_files.write(init_time.strftime('%Y-%m-%d %H:%M:%S') + '\n')
        else:
            for entry in missing:
                missing_files.write(entry + '\n')
        

        
    ok_files.close()
    missing_files.close()
    
def check(config, init_time):
    
    logger = loghelper.get(LOGGER)

    bdy_interval = config['bdy_interval']
    fcst_hours = config['simulation_length']
    
    bdy_times = shared.get_bdy_times(init_time, fcst_hours, bdy_interval)

    missing_files = []
    for key,entry in config['ungrib'].items():
        # apply any delay and rounding to the init_time to get correct time for dataset
        # note that sometimes it is necessary to use a different time e.g. for SST field is delayed by one day

        base_time = shared.get_time(init_time, delay=entry.get('delay'), round=entry.get('cycles'))
        ungrib_len = int(entry['ungrib_len'])
        bdy_times = shared.get_bdy_times(base_time, ungrib_len, bdy_interval)
   
        file_pattern = entry['files']
        
        # create an ordered set to ensure filenames only appear once
        filenames = shared.ordered_set([substitute.sub_date(file_pattern, init_time=base_time, valid_time=t) for t in bdy_times])

        for f in filenames:
            if os.path.exists(f):
                logger.debug("%s - ok" % f)
            else:
                logger.error("%s  -  missing" % f)
                missing_files.append(f)
                
            
                
    ok = missing_files==[]
    msg = 'ok' if ok else 'missing'
    logger.info("checked %s : %s " % (init_time, msg))
    return missing_files
    

        
if '__main__' in __name__:
    main()
