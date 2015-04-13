""" 
=====================================
shared helper functions for wrftools
=====================================
"""

import os
import subprocess
import sys
import shutil
import re
import traceback
import math

import glob
import time, datetime
from dateutil import rrule
from collections import OrderedDict
from namelist import Namelist, read_namelist
from queue import QueueError
import glob
import loghelper
from loghelper import create_logger
from substitute import sub_date, expand
import queue

#*****************************************************************
# Constants
#*****************************************************************
LOGGER         = 'wrf_forecast'
HOUR = datetime.timedelta(0, 60*60)                 


#****************************************************************
# Checking
#*****************************************************************
def check_config(config):
    """Ensures that certain reuqired fields are present.
    
    Does this very simply, letting dictionary raise an KeyError if 
    something is missing. Hopefully python doesn't use a clever interpreter
    which figures out that this block can be skipped! """
    
    config['domain']
    config['model']
    config['model_run']
    config['max_dom']

    

def set_only_stages(config, stages):
    """Overwrides individual stages if --only option has been specified. 
    
    Args
       config -- the configuration dictionary
       stages -- a list of registered stages"""
    
    # modify a copy, probably best practice rather than 
    # modifying the original. 
    
    result = config.copy()
    only = config.get('only')

    if type(only)==type(""): only=[only]

    # set all other stages to false
    for stage in stages:
        result[stage] = False
    
    for stage in only:
        if stage in stages:
            result[stage] = True
                
    return result
            
    
    

#*****************************************************************
# Logging
#*****************************************************************
def get_logger():
    return loghelper.get_logger(LOGGER)


def shutdown():
    loghelper.shutdown()
    
    
#******************************************************************************
# Exception handling - not sure if this is the best implementation?
#******************************************************************************
def handle(e, fail_mode, full_trace=False):
    """Logs an exception, and call sys.exit if fail_mode=='QUIT', otherwise returns 
    to allow programme to continue """
    logger    = get_logger()
  
    logger.error(str(e))
    if full_trace:
        tb = traceback.format_exc()
        logger.error(tb)
    if fail_mode.upper()=='EXIT':
        sys.exit()

#******************************************************************************
# Writing status
#******************************************************************************        
def status(config):
    """Writes a json file specifying the model status"""
    import json
    # somewhere the order gets reversed
    status = OrderedDict({ 
                "Forecast started"    : config['simulation.start'].strftime('%Y-%m-%d %H:%M'),
				"Forecast completed"  : config['simulation.complete'].strftime('%Y-%m-%d %H:%M'),
                "Model initialised"   : config['init_time'].strftime('%Y-%m-%d %H:%M'),
                "Boundary conditions" : config['bdy_conditions']})
   
    f = open(config['status_file'], 'w')
    f.write(json.dumps(status, indent=4))
    f.close()
        
        

def fill_template(template, output, replacements):
     """Replaces placeholders in template file with corresponding
     values in dictionary of replacements, and writes file to output

    Arguments:
        template     -- filename path of template file
        output       -- filename path of output file
        replacements -- dictionary with string keys and values, keys ocuuring in template
                        are replaced by values in output.
     """
     
     
     i = open(template, 'r')
     content = i.read()
     for key in replacements.keys():
        content = content.replace(key,str(replacements[key]))

     o = open(output, 'w')
     o.write(content)
     o.close()
     i.close()
     return output     


        
#******************************************************************************
# Running commands
#******************************************************************************
def env_var(expr):
    """determines whether an expression is setting an environment variable
    before a script is executed, e.g A=1 cmd"""

    return "=" in expr
    

    
def get_exe_name(cmd):
    """returns the executable name stripped of any path and arguments"""

    # a command may not be the first token, for example
    # ENV_VAR=var cmd
    
    #
    # Either cmd, or cmd args other_stuff
    #
    tokens = cmd.split()
    
    
    if len(tokens)==0:
        executable = cmd
    else:
        # eclude all environment variable definitions
        parts = [t for t in tokens if not env_var(t)]
        executable = parts[0]

    exe = os.path.split(executable)[-1]
    return exe

def get_env_vars(cmd):
    """returns any environment variable specifications supplied as prefixes to 
    the command, as e.g. A=1 B=2 my_script"""
    
    env_vars = [t for t in cmd.split() if env_var(t)]
    
    
    
    
def run(cmd, config, from_dir=None, env_vars=None):
    """ An all-purpose function to determine how a command should be run. 
    This looks in the config, and determined whether the command is to be run
    directly at the command line, at the command line via mpirun, or by 
    packaged up into a job script and submitted to the scheduler
    
    Arguments:
        cmd      -- executable to run 
        config   -- configuration specifying number of processors etc 
        env_vars -- optional dictionary of environment variables for this specific script
        from_dir -- optional directory to run the the script from
    """
    
    logger=get_logger()
    exec_name  = get_exe_name(cmd)
    queue      = config['queue']
    num_procs  = config['num_procs']
    queue_log  = config['queue_log']
    
    
    n = num_procs[exec_name] if exec_name in num_procs else 1
    
    from_dir = from_dir if from_dir else config['working_dir']
    
    # if a queue name is specified and is not false
    if exec_name in queue and queue[exec_name]:
        run_queue(cmd,config,from_dir,queue_log[exec_name], env_vars=env_vars)
        
    elif n>1:
        mpirun(cmd, n, config['host_file'], config['run_level'],config['cmd_timing'], env_vars=env_vars)
    
    else:
        run_cmd(cmd, config, env_vars=env_vars)



def mpirun(cmd, num_procs, hostfile, run_level, cmd_timing=False, env_vars=None):
    """Wrapper around the system mpirun command.
    
    Arguments:
        @cmd       -- path of the executable
        @num_procs -- int or dict specifying number of processors. If dict, executable name (not full path) used as key
        @hostfile  -- path to machine file, use 'None' to not use a host file
        @run_level -- string: 'RUN' command will get run, anything else command is logged but not run
        @cmd_timing -- boolean flag,if True, timing information logged"""
    
    logger = get_logger()
    exe = os.path.split(cmd)[1]
    
    if type(num_procs) == type({}):
        nprocs = num_procs[exe]
    else:
        nprocs = num_procs

    # LD_LIBRARY_PATH is an ungly hack to get it to work 
    # on Maestro, hopefully we can get rid of reliance on 
    # this
    env_var_str = ""
    
    if env_vars:
        env_var_str = " ".join(["-x %s=%s" %(key,value) for key,value in env_vars.items()])
        logger.debug(env_var_str)
    
    if hostfile=='None':
        cmd = 'mpirun -x LD_LIBRARY_PATH %s -n %d %s' % (env_var_str, nprocs, cmd)

    else:
        cmd = 'mpirun -x LD_LIBRARY_PATH %s -n %d -hostfile %s %s' % (env_var_str, nprocs, hostfile, cmd)

    logger.debug(cmd)
    
    t0          = time.time()
    
    if run_level.upper()=='RUN':
        ret = subprocess.call(cmd, shell=True)        
   
    telapsed = time.time() - t0
    if cmd_timing:
        logger.debug("done in %0.1f seconds" %telapsed)


        

def run_cmd(cmd, config, env_vars=None):
    """Executes and logs a shell command. If config['run_level']=='DUMMY', then
    the command is logged but not executed."""
    
    logger = get_logger()
    
    run_level   = config['run_level'].upper()
    cmd_timing  = config['cmd_timing']
    t0          = time.time()
    logger.debug(cmd)
    
    env_var_str = ""
    if env_vars:
        env_var_str = " ".join(["%s=%s" %(key,value) for key,value in env_vars.items()])
    
    cmd_str = "%s %s" %(env_var_str, cmd)
    
    #
    # Only execute command if run level is 'RUN', 
    # otherwise return a non-error 0. 
    #
    if run_level=='RUN':
        ret = subprocess.call(cmd_str, shell=True)
    else:
        ret = 0
    
    telapsed = time.time() - t0
    if cmd_timing:
        logger.debug("done in %0.1f seconds" %telapsed)
    
    return ret


def run_queue(cmd,config, run_from_dir, log_file, env_vars=None):
    """ Run a command via the scheduler, and wait in loop until
    command is expected to finish.
    
    Arguments:
        @cmd            -- full path of the executable
        @config         -- all the other settings!
        @run_from_dir   -- directory to run from 
        @log_file       -- redirect to different log file
        @env_vars       -- optional dict of environment vars"""
    
    logger          = get_logger()    

    run_level       = config['run_level']
    num_procs       = config['num_procs']
    job_template    = config['job_template']
    job_script      = config['job_script']
    queue_dict      = config['queue']
    poll_interval   = config['poll_interval']
    max_job_time    = config['max_job_time']

    exe = get_exe_name(cmd)
    

    if log_file:
        log = log_file
    else:
        log = exe

        

    try:
        qname = queue_dict[exe]
        template = job_template[qname]
        nprocs =  num_procs[exe] if exe in num_procs else 1
        mjt = max_job_time[exe]
        pint = poll_interval[exe]        

    except KeyError, e:
        tb = traceback.format_exc()
        raise ConfigError(tb)    
    

    attempts = mjt / pint
    
    #logger.debug('Submitting %s to %d slots on %s, polling every %s minutes for %d attempts' %(exe, nprocs, qname, pint, attempts ))
    #logger.debug('Running from dir: %s ' % run_from_dir)
    
    env_var_str = ""
    if env_vars:
        #logger.debug("environment variables supplied")
        
        # for older mpi versions
        env_var_str = " ".join(["-x %s=%s" %(key,value) for key,value in env_vars.items()])
        
        # mca_base_env_list" parameter to specify the whole list of required
        # environment variables. With this new mechanism, -x env_foo1=bar1 -x env_foo2=bar2
        # becomes -mca mca_base_env_list "env_foo1=bar1;env_foo2=bar2".
        #env_var_str = "-mca";".join(["%s=%s" %(key,value) for key,value in env_vars.items()])                
        
        cmd = "%s %s" %(env_var_str, cmd)
        #logger.debug(env_var_str)
        
    replacements = {'<executable>': cmd,
                '<jobname>': exe,
                '<qname>'  : qname,
                '<nprocs>' : nprocs,
                '<logfile>': log}

    fill_template(template,job_script,replacements)
    job_script      = config['job_script']
    #logger.debug("job_template: %s " % job_template)
    #logger.debug("job_script: %s "   % job_script)
    os.chdir(run_from_dir)
    
    if run_level.upper()!='RUN':
        return


    job_id = queue.qsub(job_script)
   
    for i in range(attempts):
        output = queue.qstat(job_id)
        if output=='':
            #logger.debug('no queue status for job, presume complete')
            return
        
        logger.debug(output)
        tokens =  output.split()
        status = tokens[4].strip()

        if 'E' in status:
            raise QueueError('job %s has queue status of %s' %(job_id, status))

        time.sleep(pint*60)

    # what to do?
    logger.error('Job did not complete within max number of poll attempts')
    logger.error('Suggest changing max_job_time in config file')
    raise QueueError('job %s has queue status of %s' %(job_id, status))

    
#*****************************************************************
# File manipulation/linking
#*****************************************************************
def link(pattern):
    """ Processes a link specified in the format
    source --> dest, and creates links.
    
    'source' and 'dest' will be passed directly to a sytem call to ln -sf """
    logger=get_logger()
    arg = pattern
    cmd = 'ln -sf %s ' % arg
    logger.debug(cmd)
    subprocess.call(cmd, shell=True)
    
    
    
def transfer(flist, dest, mode='copy', debug_level='NONE'):
    """Transfers a list of files to a destination.
    
    Arguments:
        @flist       -- source files to be copied/moved
        @dest        -- destination directory
        @mode        -- copy (leave original) or move (delete original). Default 'copy'
        @debug_level -- what level to report sucess/failure to """
    logger = get_logger()
    #logger.info(' *** TRANSFERRING %d FILES TO %s ***' %(len(flist), dest))
    
    n=0
    if type(flist)!=type([]):
        flist = [flist]
    
    for f in flist:
        fname = os.path.split(f)[1]
        dname = '%s/%s' % (dest, fname)

        # bit dangerous, could delete then fail?
        if os.path.exists(dname):
            os.remove(dname)

        shutil.copy2(f, dname)
        if mode=='move': os.remove(f)                        
        n+=1

    #logger.info(' *** %d FILES TRANSFERRED ***' % n )

def rsync(source, target, config):
    """ Calls rysnc to transfer files from source to target.
    If config['archive_mode']=='MOVE', then source files will be deleted
    using --remove-sent-files"""
            
    logger = get_logger()  
    archive_mode = config['archive_mode']
    logger.debug('synching %s -----> %s' % (source, target))

    if archive_mode == 'COPY':
        base_cmd = 'rsync -a --recursive %s %s'
    
    elif archive_mode == 'MOVE':
        base_cmd = 'rsync -a --recursive --remove-sent-files %s %s'
    
    cmd = base_cmd %(source, target)    
    run_cmd(cmd, config)
    
    
    
#*****************************************************************
# Datetime/filename generation functions
#*****************************************************************

def get_fcst_times(config):
    """ Return a list of datetimes representing forecast times 
    
    Reads the init_time, fcst_hours and history_interval entries 
    from config and returns a list of datetime objects representing the 
    forecast times.

    Arguments:
    config -- dictionary od configuration settings

    """
    logger           = get_logger()
    logger.debug("get_fcst_times called")
    
    init_time        = config['init_time']
    fcst_hours       = config['fcst_hours']
    history_interval = config['history_interval']
    hour             = datetime.timedelta(0, 60*60)
    minute           = datetime.timedelta(0, 60) 
    end_time         = init_time + fcst_hours*hour
    
    
    logger.debug('init_time: %s'  %init_time)
    logger.debug('fcst_hours: %s' %fcst_hours)
    logger.debug('history_interval: %s' % history_interval)
   
    freq          = rrule.MINUTELY
    rec           = rrule.rrule(freq, dtstart=init_time, until=end_time+minute, interval=history_interval)
    fcst_times    = list(rec)
    logger.debug("Forecast start: %s \t end: %s" %(fcst_times[0], fcst_times[-1]))
    return fcst_times
    

def get_operational_init_time(config):
    """ Returns a list of most recent init times for an operational forecast 
    
    Updated, if config['operational']==True
    
    Arguments:
    config -- dictionary of configuration settings            
    
    """
    
    logger        = get_logger()

    fcst_hours    = config['fcst_hours']
    operational   = config['operational']
    cycles        = config['cycles']
    gm_delay      = int(config['delay'])
    
   
        
    #
    # We want to find the most recent set of boundary conditions. Ie the nearest 6-hours
    # we could either use gribmaster to check and then get the relevant times from the 
    # filenames, or we could work out which files we want first.  Either way we need to avoid 
    # running the same forecast multiple times.
    #
    # We may want to implement a delay here to avoid asking for grib files we know don't exist
    #
    #
    #
    hour          = datetime.timedelta(0, 60*60)
    today         = datetime.datetime.today()
    delayed_time  = today - gm_delay * hour
        
    start_day     = datetime.datetime(delayed_time.year, delayed_time.month, delayed_time.day, 0, 0)           # throw away all time parts
    start_hour    = delayed_time.hour
    past_cycles   = [ c for c in cycles if (c <= start_hour)]
    recent_cycle  = past_cycles[-1]
    start         = start_day + recent_cycle * hour
    end           = start
    #config['cycle'] = recent_cycle
    #logger.debug("getting most recent operational case: %s" % start)
    #logger.debug("system current time and date: %s" % today)
    #logger.debug("but grib delay set is %s" % gm_delay)
    #logger.debug("so current time accounting for delay is: %s" % delayed_time)
    #logger.debug("start of the that day is: %s" % start_day)
    #logger.debug("most recent cycle of interest: %s" % recent_cycle)
    #logger.debug("and setting end time to be the same: %s" % end)

    return start

def get_init_times(config):
    """ Returns a list of datetimes representing initial times in a forecast test case
    
    Reads the start, end and init_interval from config and returns a list of 
    datetime objects representing the initial times
    
    Arguments:
    config -- dictionary of configuration settings            
    
    """

    logger        = get_logger()
    #logger.debug("get_init_times called")
    
    operational   = config['operational']
    start         = config['start']
    end           = config['end']
    init_interval = config['init_interval']
    freq          = rrule.HOURLY
    
    logger.debug("get_init_times called:")
    logger.debug("\t operational: %s" % operational)
    logger.debug("\t start: %s" % start)
    logger.debug("\t end: %s" % end)
    logger.debug("\t freq: %s" % freq)
    logger.debug("\t init_interval: %s" % init_interval)
    
    
    if operational:
        start = get_operational_init_time(config)
        end = start

    if type(start)!=type([]):
        start= [start]
    if type(end)!=type([]):
        end = [end]


    if len(start)!=len(end):
        raise IOError('different start and end times specified')

    init_times = []
    hour = datetime.timedelta(0,60*60)
    for s, e in zip(start, end):
        rec  = rrule.rrule(freq, dtstart=s, until=e, interval=init_interval)
        logger.debug(list(rec))
        init_times.extend(list(rec))


    for t in init_times:
        logger.debug("\t %s" %t)
    logger.debug("get_init_times done \n")
    return init_times

def get_bdy_times(config):
    """ Returns a list of datetime objects representing the times of boundary conditions.
    
    Read the init_time, fcst_hours and bdy_interval from config
    and returns a list of datetime objects representing the 
    boundary condition times. 
    
    Arguments:
    config -- dictionary of configuration settings    
    
    """
    
    logger        = get_logger()
    logger.debug("get_bdy_times called")
    init_time     = config['init_time']
    fcst_hours    = config['fcst_hours']
    bdy_interval  = config['bdy_interval']
    hour          = datetime.timedelta(0, 60*60) 
    end_time      = init_time + datetime.timedelta(0, fcst_hours*60*60)
    
    
    #
    # Get the range of files representing boundary condition files
    # Because rrule is not inclusive, we add one hour on to the end 
    # time to make it so
    #                                                                  
    freq         = rrule.HOURLY
    rec          = rrule.rrule(freq, dtstart=init_time,until=end_time+hour, interval=bdy_interval)
    bdy_times    = list(rec)
    #logger.debug("got the following boundary condition times:")
    #for t in bdy_times:
    #    logger.debug("%s" %t)
    
    return bdy_times
    

def get_bdy_filenames(grb_fmt, bdy_times):
    """ Creates a list of boundary conditions filenames
    based on the information in config. In general this will 
    be called once per forecast, so there is only one 
    init_time.
   
    Arguments:
    config -- dictionary containing various configuration options
    
    """

    logger       = get_logger()
    logger.debug('*** GENERATING BOUNDARY CONDITION FILENAMES ***')
   
    filelist = [sub_date(grb_fmt, init_time=bdy_times[0], valid_time=b) for b in bdy_times]
    logger.debug(filelist)
    return filelist    
    
def get_sst_time(config):

    init_time      = config['init_time']    
    sst_delay      = config['sst_delay']    
    delta          = datetime.timedelta(0, sst_delay*60*60)
    delayed_time   = init_time - delta
    # we need to make sure this is only 00 hour
    sst_time       = datetime.datetime(delayed_time.year, delayed_time.month, delayed_time.day, 0, 0, 0) 
    return sst_time

def get_sst_filename(config):
    base_filename  = config['sst_filename']
    sst_time       = get_sst_time(config)
    sst_filename   = sub_date(base_filename, init_time=sst_time)
    return sst_filename
    
    
def _prior_time(basetime, hours=None, delay=None):
    """ Gets the closest prior time to basetime, restricted to to specified hours
    
    Arguments:
        basetime -- a datetime object of the time work from
        hours    -- a list of integers representing hours to round to
        
    Returns a datetime object representing the closest prior time to basetime which 
    is a whole number of hours """

    hour          = datetime.timedelta(0, 60*60)

    if delay:
        basetime = basetime - delay*hour

    if hours:
        start_day     = datetime.datetime(basetime.year, basetime.month, basetime.day, 0, 0)           # throw away all time parts
        start_hour    = basetime.hour
        past_hours   = [ h for h in hours if (h <= start_hour)]
        recent_hour  = past_hours[-1]
        prior        = start_day + recent_hour * hour
        return prior
        
    else:
        return basetime
    
def _listify(element):
    """ Ensures elements are contained in a list """
    
    # either it is a list already, or it is None
    if type(element)==type([]) or element==None:
        return element
    
    else:
        return [element]
