#
# Provides support for running and querying jobs using the
# PBS job submission mechanism. Basically a series of thin 
# wrappers around the qsub and qstat commands.
#
import time
import wrftools

def qsub(job_script):
    """Submits a PBS job via qsub
    
    Arguments:
        @job_script -- full path to a pbs job script file
        
    Returns:
        @job_id -- the job id returned by the PBS system """
    logger = wrftools.get_logger()
    logger.debug('submitting job %s' % job_script)
    pass
    
    
def poll(job_id):
    """Polls the PBS system, and returns the status of the job_id.
    Arguments:
        @job_id -- the PBS job id to poll
    
    Returns:
        @ status code of the job w: waiting  etc etc. """
        
    pass        
    
    
def test():
    logger = wrftools.get_logger()    
    job_id = qsub('test.pbs')
    status = poll(job_id)
    for i in range(10):
        status = poll(job_id)
        logger.debug(status)
        

if "__main__" in __name__:
    test()        