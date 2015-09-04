""" Recursively replace placholder expressions with time and date fields in all files within a directory

Config comes from a file, specified as --config argument. Some configuration options (listed below) 
can also be given at the command line, where they will override the configuration file. 
See example/templater.yaml for a full list of configuration options. 


Usage:
    templater.py [--config=<file>] [options]
    
Options:
    --config=<file>         yaml/json file specifying configuration options
    --source=<source>       source file or directory to read from, directories processes recursively
    --target=<target>       target file or directory to write to. Is source is directory, structure of target will mirror source
    --template-expr=<expr>  expression in templates which indicates placeholder to be expanded (default <%s>)
    --start=<time>          an initial time to work with, if not specified, init time will be caculated from base-time, delay and cycles
    --base-time=<time>      a base-time to calculate start time from, if not present, system time is used
    --delay=<hours>         number of hours delay to apply to base-time
    --cycles=<hours>        list of hours to restrict start times to e.g. [0,12]
    --end=<time>            an end initial time for the simulation blocks. If not specified, a single simulation assumed
    --init-interval=<hours> number of hours between initialistions, use in combination with end
    --working-dir=<dir>     working directory specifier which may contain date and time placeholders, see below
    --dry-run               log but don't execute commands
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
from confighelper import confighelper as conf
import substitute


def main():
    # merge command-line and file-specified arguments
    config = conf.config(__doc__, sys.argv[1:])

    logger = loghelper.create(LOGGER, log_level=config.get('log.level'), log_fmt=config.get('log.format'))

    if config.get('log.file'):
        log_file = config['log.file']
        logger.addHandler(loghelper.file_handler(log_file, config['log.level'], config['log.format']))
        logger.debug('now logging to file')
    
    dry_run = config.get('dry-run')
    
    # either the start time is exactly specified, or else we calculate it
    if config.get('start'):
        init_time = config['start']
    else:
        init_time = shared.get_time(base_time=config.get('base-time'), delay=config.get('delay'), round=config.get('cycles'))

    if config.get('end'):
        end_init = config['end']
        init_interval = config['init_interval']
        init_times = list(rrule.rrule(freq=rrule.HOURLY, interval=init_interval, dtstart=init_time, until=end_init))
    else:
        init_times = [init_time]


    for init_time in init_times:
        # one-argument function to do initial-time substitution in strings
        expand = lambda s : substitute.sub_date(s, init_time=init_time) if type(s)==type("") else s
        
        # dictionary of replacements e.g. %iY : 2015
        date_replacements = substitute.date_replacements(init_time=init_time)
        
        source = expand(config['source'])
        target = expand(config['target'])
        
        assert(_are_compatible(source,target))

        _recursive_replace(source, target, date_replacements)


def fill_template(template, target, replacements):
    """Replaces placeholders in template with corresponding
    values in dictionary replacements

    Arguments:
        template -- the source filename
        target -- the target filename to write to

    Returns the target filename"""
     
    with open(template) as i:
        content = i.read()

    for key in replacements.keys():
        content = content.replace(key,str(replacements[key]))

    # path = os.path.split(target)[0]
    # if not os.path.exists(path):
        # os.makedirs(path)
    
    with open(target, 'w') as o:
        o.write(content)
    
    return target     
        

def _recursive_replace(source_dir, target_dir, replacements):
    logger=loghelper.get(LOGGER)
    """recursively make replacements to files in source_dir to target_dir"""
    # from os.walk
    # dirpath is a string, the path to the directory. 
    # dirnames is a list of the names of the subdirectories in dirpath (excluding '.' and '..'). 
    # filenames is a list of the names of the non-directory files in dirpath. 
    # Note that the names in the lists contain no path components. To get a full path (which begins with top) to a file or directory in dirpath, do os.path.join(dirpath, name).
    logger.debug('_recursive_replace(%s, %s, replacements)' %(source_dir, target_dir))
    for dirpath, dirnames, filenames in os.walk(source_dir):

        for name in filenames:
            source = os.path.join(dirpath, name)
            target = source.replace(source_dir, target_dir)
            target_path = os.path.split(target)[0]
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            logger.debug("%s ---> %s" %(source, target))
            fill_template(source,target,replacements)
            assert(os.path.exists(target))


def _is_file(path):
    """path is a file, but not directory"""
    return os.path.isfile(path) and not os.path.isdir(path)
    
def _is_dir(path):
    """path is a file, but not directory"""
    return os.path.isdir(path)
    
def _are_compatible(source, target):
    """acceptible: source and target both files, source and target both directories, source file and target directory"""
    both_files = _is_file(source) and _is_file(target)
    both_dirs = _is_dir(source) and _is_dir(target)
    source_file_target_dir = _is_file(source) and _is_dir(target)

    accept = both_files or both_dirs or source_file_target_dir
    return accept
        
if '__main__' in __name__:
    main()