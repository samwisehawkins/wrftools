""" Submit specified job scripts

Config comes from a file, specified as --config argument. Some configuration options (listed below) 
can also be given at the command line, where they will override the configuration file. 
See example/templater.yaml for a full list of configuration options. 


Usage:
    submit.py [--config=<file>] [options]
    
Options:
    --config=<file>         yaml/json file specifying configuration options
    --start=<time>          an initial time to work with, if not specified, time will be caculated from base-time, delay and cycles
    --base-time=<time>      a base-time to calculate start time from, if not present, system time is used
    --delay=<hours>         number of hours delay to apply to base-time
    --cycles=<hours>        list of hours to restrict start times to e.g. [0,12]
    --end=<time>            an end time for the simulation blocks
    --init-interval=<hours> number of hours between initialistions
    --working-dir=<dir>     working directory specifier which may contain date and time placeholders, see below
    --template-expr=<expr>  expression in templates which indicates placeholder to be expanded (default <%s>)
    --after-job=<job>       initial job id or job name to be given as as dependency for the first job
    --parallel-sims=<N>     allow N seperate simulations to be submitted in parrallel, default is 0 (seqential) NOT IMPLEMENTED
    --dry-run               log but don't execute commands
    --log.level=<level>     log level info, debug or warn (see python logging modules)
    --log.format=<fmt>      log format code (see python logging module)
    --log.file=<file>       optional log file
    --help                  display documentation
    
The above options can all be given at the command line. Jobs must be specified inside a configuration file. See config/templater.yaml for
an example"""

LOGGER="wrftools"

import sys
import os
import loghelper
from collections import OrderedDict
from dateutil import rrule
from wrftools.confighelper import confighelper as conf
from wrftools.loghelper import loghelper
from wrftools import shared
from wrftools import queue
from wrftools import substitute
import json


def main():
    # merge command-line and file-specified arguments
    config = conf.config(__doc__, sys.argv[1:])

    logger = loghelper.create(LOGGER, log_level=config.get('log.level'), log_fmt=config.get('log.format'))
    if config.get('log.file'):
        log_file = config['log.file']
        logger.addHandler(loghelper.file_handler(log_file, config['log.level'], config.get('log.format')))
    

    
    
    dry_run = config.get('dry-run')
    after_job = config.get('after-job')
    max_dom = config['max_dom']
    
    # either the start time is exactly specified, or else we calculate it from base time, delay and cycles
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

    jobs = config['jobs']
    import json
    logger.debug(json.dumps(jobs, indent=4))
    run_jobs = OrderedDict([ (j,jobs[j]) for j in sorted(jobs.keys()) if jobs[j]['run']==True])
    logger.debug(json.dumps(run_jobs, indent=4))
    
    for init_time in init_times:
        # one-argument function to do initial-time substitution in strings
        expand = lambda s : substitute.sub_date(str(s), init_time=init_time)

        after_job = submit(run_jobs, expand, after_job=after_job, array_job=max_dom, dry_run=dry_run)
        

def submit(jobs, expand, after_job=None, array_job=None, dry_run=False):    
    """Arguments:
        jobs: job entry specification as a dictionary
        expand: function to expand any placeholders in strings
        after_id: initial job id to specify as depenpency
        array_job: number of array jobs to submit where specified"""
        
        
    job_ids = {}
    first=True
    for key,entry in jobs.items():
        script = expand(entry['script'])
        run_dir = os.path.split(script)[0]
        
        if not first and entry.get('after'):
            after_job = job_ids[entry['after']]


        array = array_job if entry.get('per-domain') else None

        job_id = queue.qsub(script, after_job=after_job, cwd=run_dir, array=array, dry_run=dry_run)
        job_ids[key] = job_id
        first=False
    
    return job_id
        
if '__main__' in __name__:
    main()