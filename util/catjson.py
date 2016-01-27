""" catjson.py concatenates multiple JSON files together into one file containg an array

Usage:
    catjson.py <files>... [--config=<file>] [options]
       
        
Options:
        <files>                   input files to operate on
        --config=<file>           file specifiying configuration options
        --log_name=<name>         name of logger, allows shared loggers between modules
        --log_level=<level>       log level, debug, info or warn
        --log_file=<file>         write log output to file as well as stdout
        --log_fmt=<fmt>           formart of log messages, see logging module for details"""


import os
import sys
import docopt
import json

result = []
config = docopt.docopt(__doc__, sys.argv[1:] )

files = config['<files>']
for f in files:
    contents = json.load(open(f))
    if type(contents)==type([]):
        result.extend(contents)
    else:
        result.append(contents)

print json.dumps(result)