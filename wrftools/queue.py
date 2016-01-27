""" Provides support for running and querying jobs using the
    SGE job submission mechanism. Basically a series of thin 
    wrappers around the qsub and qstat commands."""

import os
import time
import loghelper
import subprocess
import random
from customexceptions import QueueError

LOGGER='wrftools'     

def qsub(script, name=None, queue=None, pe=None, nslots=1, after_job=None, cwd=None, array=None, merge=True, log=None, dry_run=False):
    """Submits a SGE job via qsub
    
    Arguments:
        script -- full path to job script file
        name -- job name
        queue -- name of queue to submit to
        pe -- parallel environment to use
        nslots -- number of slots (usually processor cores)
        after_job -- job id or name to supply as dependency
        cwd -- change working directory to this before submitting
        array -- if integer N supplied, will submit array jobs 1:N
        dry_run -- log but don't submit commands (default False)
    Returns:
        job_id -- the job id returned by the sheduling system system """
 
    logger = loghelper.get(LOGGER)
    
    if not os.path.exists(script): 
        raise IOError("%s not found" % script)
    
    
    name_arg = '-N %s' % name if name else ''
    q_arg = '-q %s' % queue if queue else ''
    pe_arg = '-pe %s' % pe if pe else ''    
    nslots_arg = ' %d' % nslots if nslots else ''
    pe_slots_arg = pe_arg + nslots_arg
    after_arg = '-hold_jid %s' % after_job if after_job else ''
    cwd_arg = '-cwd' if cwd else ''
    array_arg = '-t 1-%s' % array if array else ''
    merge_arg = '-j y' if merge else ''
    log_arg = '-o %s' % log if log else ''
    
    all_args = ' '.join([name_arg,q_arg,pe_slots_arg,after_arg,cwd_arg,array_arg,merge_arg,log_arg])
    
    
        
    
    cmd  = 'qsub %s %s ' % (all_args, script)
    
    
    if dry_run:
        job_id = str(random.randint(1,100))
    else:
        proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True, cwd=cwd, executable='/bin/bash')
        output = proc.stdout.read()
        job_id = job_id_from_reponse(output)

    logger.debug("%s \t--->\t %s" % (cmd.ljust(150), job_id))
    return job_id
    
def job_id_from_reponse(text): 
    """Return a string representation of integer job id from the qsub response to stdout"""
    #
    # The output from SGE is of the form
    # "Your job 3681 ("TEST") has been submitted"
    # Your job-array 4321.1-3:1 ("wrfpost") has been submitted
    #

    job_id = text.split(' ')[2]
    
    if "." in job_id:
        # job was an array job
        job_id = job_id.split('.')[0]
    return job_id
    
def qstat(job_id):
    """Polls the PBS system, and returns the status of the job_id.
    Uses qstat -f | grep job_id
    Arguments:
        @job_id -- the PBS job id to poll
    
    Returns:
        @ status code of the job w: waiting  etc etc. """
        
    cmd = 'qstat -f | grep %s' % job_id
    proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    output = proc.stdout.read().rstrip('\n')
    return output


if __name__ == "__main__":
    test()        