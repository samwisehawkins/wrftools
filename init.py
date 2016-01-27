""" Generate master job scripts from a configuration file

Config comes from a file, specified as --config argument. Some configuration options (listed below) 
can also be given at the command line, where they will override the configuration file. 


Usage:
    init.py [--config=<file>] [options]
    
Options:
    --base_dir=<dir>        directory to initialise (specify at command line, not in file)
    --config=<file>         yaml/json file specifying configuration options
    --template-dir=<dir>    directory containing job template
    --target-dir=<dir>      directory to write scripts into
    --log.level=<level>     log level info, debug or warn (see python logging modules)
    --log.format=<fmt>      log format code (see python logging module)
    --log.file=<file>       optional log file
    --help                  display documentation
    
The above options can all be given at the command line. Jobs must be specified inside a configuration file. See config/initialise.yaml for
an example"""


NEXT_STEPS = """base directory %s initialised. Next do the following: 

1. Copy namelist.wps and namelist.input files into the base directory. 

2. Check and edit the master scripts inside %s/scripts

3. Edit prepare.yaml 

4. $>python prepare.py --config=prepare.yaml --link-boundaries

5. Check directory structure

6. Edit submit.yaml

7. $>python submit.py --config=submit.yaml"""


LOGGER="wrftools"

import os
import sys
import subprocess
import shutil
import loghelper
import confighelper as conf
from wrftools import templater as tm
from wrftools import shared

def main():
    # merge command-line and file-specified arguments
    config = conf.config(__doc__, sys.argv[1:])
    logger = loghelper.create(LOGGER, log_level=config.get('log.level'), log_fmt=config.get('log.format'))
    
    if config.get('log.file'):
        log_file = config['log.file']
        logger.addHandler(loghelper.file_handler(log_file, config['log.level'], config['log.format']))
    
    base_dir = config['base_dir']
    wrftools_dir = config['wrftools_dir']
    dry_run = config.get('dry_run')
    jobs = config.get('jobs')
    create = config.get('initialise.create')
    remove = config.get('initialise.remove')
    copy = config.get('initialise.copy')
    link = config.get('initialise.link')

    generate_job_scripts(jobs)
    
    if create:
        for d in create:
            shared.create(d, dry_run=dry_run)

    if remove:
        for pattern in remove:
            shared.remove(pattern, dry_run=dry_run)

    if copy:
        for pattern in copy:
            shared.copy(pattern, dry_run=dry_run)
            
    if link:
        for pattern in link:
            shared.link(pattern, dry_run=dry_run)

    logger.debug("init.py done")
    print "\n\n"
    print "************************************************"
    print NEXT_STEPS % (base_dir,base_dir)
    print "************************************************"
            
    
def generate_job_scripts(jobs):
    logger = loghelper.get(LOGGER)
    for key in sorted(jobs.keys()):
        entry = jobs[key]
        template = entry['template']
        target = entry['target']
        logger.debug("filling template  %s ----> %s" % (template, target))
        path,name = os.path.split(target)
        if not os.path.exists(path):
            os.makedirs(path)
        
        if entry.get('replacements'):
            tm.fill_template(template,target,entry['replacements'])
        else:
            shutil.copyfile(template, target)
        
if '__main__' in __name__:
    main()