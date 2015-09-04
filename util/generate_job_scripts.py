""" Generate inital job scripts from a configuration file

Config comes from a file, specified as --config argument. Some configuration options (listed below) 
can also be given at the command line, where they will override the configuration file. 
See example/templater.yaml for a full list of configuration options. 


Usage:
    generate_job_scripts.py [--config=<file>] [options]
    
Options:
    --config=<file>         yaml/json file specifying configuration options
    --template-dir=<dir>    directory containing job template
    --target-dir=<dir>      directory to write scripts into
    --log.level=<level>     log level info, debug or warn (see python logging modules)
    --log.format=<fmt>      log format code (see python logging module)
    --log.file=<file>       optional log file
    --help                  display documentation
    
The above options can all be given at the command line. Jobs must be specified inside a configuration file. See config/templater.yaml for
an example"""

LOGGER="wrftools"

import os
import sys
import loghelper
from wrftools.confighelper import confighelper as conf
from wrftools import templater as tm

def main():
    # merge command-line and file-specified arguments
    config = conf.config(__doc__, sys.argv[1:])

    logger = loghelper.create(LOGGER, log_level=config.get('log.level'), log_fmt=config.get('log.format'))

    if config.get('log.file'):
        log_file = config['log.file']
        logger.addHandler(loghelper.file_handler(log_file, config['log.level'], config['log.format']))
   
    jobs = config['jobs']
    
    for key in sorted(jobs.keys()):
        entry = jobs[key]
        template = entry['template']
        target = entry['target']
        logger.debug("filling template  %s ----> %s" % (template, target))
        path,name = os.path.split(target)
        if not os.path.exists(path):
            os.makedirs(path)
        
        replacements = entry['replacements']
        tm.fill_template(template,target,replacements)
        
if '__main__' in __name__:
    main()