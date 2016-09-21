""" Get the inital time for a simulation based on supplied arguments

Config comes from a file, specified as --config argument. Some configuration options (listed below) 
can also be given at the command line, where they will override the configuration file. 
See example/forecast.yaml for a full list of configuration options. 

Usage:
    times.py [--config=<file>] [--start=<time>] [--end=<time>] [--interval=<hours>] [--delay=<hours>] [--cycles=<hours>] [--format=<fmt>]
    
Options:
    --config=<file>         yaml/json file specificying any of the options below
    --start=<time>          an initial time to start simulation from, if not specified, system time will be used
    --delay=<hours>         number of hours delay to apply to start time
    --cycles=<hours>        list of hours to restrict start times to e.g. [0,12]
    --format=<fmt>          date format code default '%Y-%m-%d_%H:%M:%S' """

import sys
import confighelper as conf
from wrftools import shared    

def main():
    # merge command-line and file-specified arguments
    config = conf.config(__doc__, sys.argv[1:])

    start = shared.get_time(config.get('start'), config.get('delay'), config.get('cycles'))
    end = shared.get_time(config.get('end'), config.get('delay'), config.get('cycles'))
    
    
    interval = config['interval'] if config.get('interval') else 24
    init_times = shared.get_init_times(start, end, interval)
    format = config['format'] if config.get('format') else '%Y-%m-%d %H:%M:%S'
    
    
    for init_time in init_times:
        print(init_time.strftime(format))

    
if '__main__' in __name__:
    main()