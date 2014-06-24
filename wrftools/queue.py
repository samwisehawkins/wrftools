""" Provides support for running and querying jobs using the
    PBS job submission mechanism. Basically a series of thin 
    wrappers around the qsub and qstat commands."""

import os
import time
import loghelper
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
 
    logger = loghelper.get_logger('wrf_forecast')
    #logger.debug('submitting job %s' % job_script)
    
    cmd  = 'qsub %s ' % job_script
    logger.debug(cmd)
    
    #
    # The output from PBS is of the format
    # "Your job 3681 ("TEST") has been submitted"
    #
    proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    output = proc.stdout.read()
    job_id = output.split(' ')[2]
    logger.debug("job submitted with ID: %s" % job_id)
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



def test():
    loghelper.get_logger('wrf_forecast')
    print('running test')
    #logger.debug('running test')
    

    template   = '/home/slha/code/wrftools/devel/queue/template.sge'
    job_script = '/home/slha/code/wrftools/devel/queue/job.sge'
    executable = '/home/slha/forecasting/development/run/wrf.exe'
    run_dir    = '/home/slha/forecasting/development/run'
    jobname    = 'WRF'
    qname      = 'all.q'
    nprocs     = 8
 
    replacements = {'<executable>': executable,
                    '<jobname>': jobname,
                    '<qname>'  : qname,
                    '<nprocs>' : nprocs}
    
    fill_template(template, job_script, replacements)

    os.chdir(run_dir)
    job_id = qsub(job_script)
    
    for i in range(3):
        status = qstat(job_id)
        print status
        if status==None:
            'print job not in queue, presume complete'
            break
        if 'E' in status:
            raise QueueError('job %s has queue status of %s' %(job_id, status))
        

        time.sleep(5)

if __name__ == "__main__":
    test()        