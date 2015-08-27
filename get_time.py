""" Get the inital time for a simulation based on supplied arguments

Config comes from a file, specified as --config argument. Some configuration options (listed below) 
can also be given at the command line, where they will override the configuration file. 
See example/forecast.yaml for a full list of configuration options. 

Usage:
    get_time.py [--config=<file>] [options]
    
Options:
    --config=<file>         yaml/json file specificying any of the options below
    --start=<time>          an initial time to start simulation from, if not specified, system time will be used
    --delay=<hours>         number of hours delay to apply to start time
    --cycles=<hours>        list of hours to restrict start times to e.g. [0,12]
    --format=<fmt>          date format code default '%Y-%m-%d_%H:%M:%S' """

import sys
from wrftools.confighelper import confighelper as conf
from wrftools import shared    

def main():
    # merge command-line and file-specified arguments
    config = conf.config(__doc__, sys.argv[1:])

    init_time = shared.get_time(config.get('start'), config.get('delay'), config.get('cycles'))
    format = config['format'] if config.get('format') else '%Y-%m-%d_%H:%M:%S'
    
    print init_time.strftime(format)

    
if '__main__' in __name__:
    main()