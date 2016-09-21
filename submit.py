""" Submit specified job scripts

Config comes from a file, specified as --config argument. Some configuration options (listed below) 
can also be given at the command line, where they will override the configuration file. 
See config/submit.yaml for a full list of configuration options. 


Usage:
    submit.py --config=<file> [--dry-run] [--working-dir=<dir>] [--parallel=<N>] [--after-job=<job>] [--log.level=<level>] [--log.format=<fmt>] [--log.file=<file>] <init_times>
    
Options:
    --config=<file>         yaml/json file specifying configuration options
    --working-dir=<dir>     working directory specifier which may contain date and time placeholders, see below
    --after-job=<job>       initial job id or job name to be given as as dependency for the first job
    --parallel=<N>          submit N simulations in parallel
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
from dateutil import rrule, parser
import confighelper as conf
import loghelper
from wrftools import shared
from wrftools import queue
from wrftools import substitute
import json


def main():
    # merge command-line and file-specified arguments
    config = conf.config(__doc__, sys.argv[1:])

    logger = loghelper.create(LOGGER, log_level=config.get('log.level'), log_fmt=config.get('log.format'),log_file=config.get('log.file'))
    
    init_file = config['<init_times>']
    if not os.path.exists(init_file):
        raise IOError("can not find file specifying initial times: %s " % init_file)

    f = open(init_file, 'r')
    content = f.read().rstrip()
    f.close()
    init_strings = content.split('\n') 
    logger.debug(init_strings)
    # allow format often used by WRF, with an underscore seperating date and time
    init_strings = [s.replace('_', ' ') for s in init_strings]
    init_times = [ parser.parse(token) for token in init_strings]
    
    
    dry_run = config.get('dry-run')
    after_job = config.get('after-job')
    max_dom = config['max_dom']
    

    jobs = config['jobs']


    
    run_jobs = [ j for j in jobs if true_like(j['run'])]
    
    parallel = int(config.get('parallel'))
    logger.debug("allow %d parallel simulations" % parallel)
    
    after_job=None
    previous_sim=None
    working_dir = config.get('working-dir')
    for n,init_time in enumerate(init_times):
        # one-argument function to do initial-time substitution in strings
        expand = lambda s : substitute.sub_date(str(s), init_time=init_time)
        wdir = expand(working_dir)
        if not os.path.exists(wdir):
            logger.error("could not find %s, skipping" % wdir)
            continue
        # allow individual simulations to run in parallel, but up to a limit of N
        # every time N reaches parallel limit, enforce a dependency

        if parallel==0 or (n%parallel)==0:
            after_job=previous_sim
            logger.debug("dependency: %s" % after_job)        
        previous_sim = submit(run_jobs, expand, after_job=after_job, array_job=max_dom, dry_run=dry_run)
        


        
def submit(jobs, expand, after_job=None, array_job=None, dry_run=False):    
    """Submits specicfied jobs to a scheduling engine e.g. SGE
    
    Arguments:
        jobs     : job entry specification as a dictionary
        expand   : function to expand any placeholders in strings
        after_id : initial job id to specify as depenpency
        
    Returns:
        The final job_id submitted"""
        
    logger = loghelper.get(LOGGER)
    logger.debug("submitting jobs")
    job_ids = {}
    first=True
    for entry in jobs:
        name = expand(entry['name'])
        script = expand(entry['script'])
        run_dir = os.path.split(script)[0]

        
        # job dependency can either come from entry, or from previous simulation
        if not first and entry.get('after'):
            after_job = entry['after']

        job_id = queue.qsub(script, name=entry.get('name'), queue=entry.get('queue'), pe=entry.get('pe'), nslots=entry.get('nprocs'), 
                            after_job=after_job, cwd=run_dir, array=entry.get('array'), merge=True, log=entry.get('log'),
                            dry_run=dry_run)

        
        job_ids[name] = job_id
        first=False
    
    return job_id


def true_like(s):
    if s is True:
        return True
    elif type(s)==str and s.lower() != 'false':
        return True

    
if '__main__' in __name__:
    main()
