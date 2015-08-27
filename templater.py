""" Generate job scripts from templates.  

Config comes from a file, specified as --config argument. Some configuration options (listed below) 
can also be given at the command line, where they will override the configuration file. 
See example/templater.yaml for a full list of configuration options. 


Usage:
    templater.py [--config=<file>] [options]
    
Options:
    --config=<file>         yaml/json file specifying configuration options
    --start=<time>          an initial time to work with, if not specified, time will be caculated from base-time, delay and cycles
    --base-time=<time>      a base-time to calculate start time from, if not present, system time is used
    --delay=<hours>         number of hours delay to apply to base-time
    --cycles=<hours>        list of hours to restrict start times to e.g. [0,12]
    --working-dir=<dir>     working directory specifier which may contain date and time placeholders, see below
    --template-expr=<expr>  expression in templates which indicates placeholder to be expanded (default <%s>)
    --dry-run               log but don't execute commands
    --log.level=<level>     log level info, debug or warn (see python logging modules)
    --log.format=<fmt>      log format code (see python logging module)
    --log.file=<file>       optional log file
    --help                  display documentation
    
The above options can all be given at the command line. Jobs must be specified inside a configuration file. See config/templater.yaml for
an example"""

LOGGER="wrftools"

import sys
import loghelper
from wrftools.confighelper import confighelper as conf
from wrftools import shared
from wrftools import substitute

DEFAULT_TEMPLATE_EXPR = '<%s>'   


def main():
    # merge command-line and file-specified arguments
    config = conf.config(__doc__, sys.argv[1:])

    dry_run = config.get('dry-run')
    
    # either the start time is exactly specified, or else we calculate it
    if config.get('start'):
        init_time = config['start']
    else:
        init_time = shared.get_time(base_time=config.get('base-time'), delay=config.get('delay'), round=config.get('cycles'))

    # one-argument function to do initial-time substitution in strings
    expand = lambda s : substitute.sub_date(str(s), init_time=init_time)
    
    logger = loghelper.create(LOGGER, log_level=config.get('log.level'), log_fmt=config.get('log.format'))
    
    if config.get('log.file'):
        log_file = expand(config['log.file'])
        logger.addHandler(loghelper.file_handler(log_file, config['log.level'], config['log.format']))

        
    template_expr = config['template-expr'] if config.get('template-expr') else DEFAULT_TEMPLATE_EXPR
    
    jobs = config['jobs']
    for key in sorted(jobs.keys()):
        entry = jobs[key]
        template = expand(entry['template'])
        target = expand(entry['target'])
        logger.debug('%s ----->\t%s' % (template.split('/')[-1].ljust(20), target))
        replacements = generate_replacements(entry, template_expr, expand)
        date_replacements = substitute.date_replacements(init_time=init_time)
        replacements.update(date_replacements)
        shared.fill_template(template,target,replacements)


        
def generate_replacements(mapping, template_expr, expander):
    expand_key = lambda s : template_expr % s
    replacements = { expand_key(key) : expander(value) for (key,value) in mapping.items()}
    return replacements



        
        
if '__main__' in __name__:
    main()