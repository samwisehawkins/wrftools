""" Script for checking existince of boundary condition files for WRF simulation. 

Config comes from a file, specified as --config argument. Some configuration options (listed below) 
can also be given at the command line, where they will override the configuration file. 
See example/forecast.yaml for a full list of configuration options. 

Usage:
    check.py [--config=<file>] <init_times>
    
Options:
    --config=<file>         yaml/json file specificying any of the options below
    --log.level=<level>     log level info, debug or warn (see python logging modules)
    --log.format=<fmt>      log format code (see python logging module)
    --log.file=<file>       optional log file
    <init_times>            file with init times, one per line"""

LOGGER="wrftools"

import sys
import os
import shutil
import subprocess
import glob
import datetime
import collections
from dateutil import rrule, parser
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
    
    
    init_file = config['<init_times>']
    
    ok_files = open(config['ok_files'], 'w')
    missing_files = open(config['missing_files'], 'w')
    
    if not os.path.exists(init_file):
        raise IOError("can not find file specifying initial times: %s " % init_file)

    f = open(init_file, 'r')
    content = f.read().rstrip()
    f.close()
    init_strings = content.split('\n') 

    # allow format often used by WRF, with an underscore seperating date and time
    init_strings = [s.replace('_', ' ') for s in init_strings]
    init_times = [ parser.parse(token) for token in init_strings]

    
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
                #logger.error("%s \t missing" % f)

    ok = missing_files==[]
    msg = 'ok' if ok else 'missing'
    logger.info("checked %s : %s " % (init_time, msg))
    return missing_files
    

        
if '__main__' in __name__:
    main()
