""" Provides support for running and querying jobs using the
    PBS job submission mechanism. Basically a series of thin 
    wrappers around the qsub and qstat commands."""

import os
import time
import wrftools
import subprocess
from customexceptions import QueueError


def fill_template(template, output, replacements):
     """Replaces placeholders in template with corresponding
     values in dictionary replacements """
     
     
     i = open(template, 'r')
     content = i.read()
     for key in replacements.keys():
        content = content.replace(key,str(replacements[key]))

     o     = open(output, 'w')
     o.write(content)
     o.close()
     i.close()
     return output     
     

def qsub(job_script):
    """Submits a PBS job via qsub
    
    Arguments:
        @job_script -- full path to a pbs job script file
    Returns:
        @job_id -- the job id returned by the PBS system """
 
    logger = wrftools.get_logger()
    logger.debug('submitting job %s' % job_script)
    
    cmd  = 'qsub %s ' % job_script

    
    #
    # The output from PBS is of the format
    # "Your job 3681 ("TEST") has been submitted"
    #
    print cmd
    proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    output = proc.stdout.read()
    print output
    job_id = output.split(' ')[2]
    print job_id
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
    output = proc.stdout.read()
    if output==None:
        return output
    
    else:
        status = output.split()[4].strip()
        return status

def test():
    logger = wrftools.get_logger()
    print('running test')
    #logger.debug('running test')
    

    template   = '/home/slha/code/wrftools/devel/pbs/template.sge'
    job_script = '/home/slha/code/wrftools/devel/pbs/job.sge'
    executable = '/home/slha/code/wrftools/devel/pbs/test.sh'
    jobname    = 'SAM'
    qname      = 'all.q'
    nprocs     = 1
 
    replacements = {'<executable>': executable,
                    '<jobname>': jobname,
                    '<qname>'  : qname,
                    '<nprocs>' : nprocs}
    
    fill_template(template, job_script, replacements)
    job_id = qsub(job_script)
    
    for i in range(3):
        status = qstat(job_id)
        print status
        if status==None:
            'print job not in queue, presume complete'

        time.sleep(5)

if __name__ == "__main__":
    test()        