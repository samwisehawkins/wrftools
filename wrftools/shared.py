""" shared helper functions for wrftools"""

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
from .namelist import Namelist, read_namelist

import glob
import loghelper

#*****************************************************************
# Constants
#*****************************************************************
LOGGER = 'wrftools'
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
    return loghelper.get(LOGGER)


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
     for key in list(replacements.keys()):
        content = content.replace(key,str(replacements[key]))

     o = open(output, 'w')
     o.write(content)
     o.close()
     i.close()

        
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


def run_cmd(cmd, dry_run=False, cwd=None, env_vars=None, timing=False, log=True):
    """Executes and logs a shell command
    
    Arguments:
        cmd      -- the command to execute
        dry_run  -- log but don't execute commands (default false)
        env_vars -- dictionary of environment vars to prefix, e.g. ENV=value cmd
        timing   -- log elapsed time default False"""
    
    logger = get_logger()
    

    t0 = time.time()
    
    if log:
        logger.debug(cmd)
    
    env_var_str = ""
    if env_vars:
        env_var_str = " ".join(["%s=%s" %(key,value) for key,value in env_vars.items()])
    
    cmd_str = "%s %s" %(env_var_str, cmd)
    
    #
    # Only execute command if run level is 'RUN', 
    # otherwise return a non-error 0. 
    #
    if not dry_run:
        ret = subprocess.call(cmd_str, cwd=cwd, shell=True)
    else:
        ret = 0
    
    telapsed = time.time() - t0
    if timing and log:
        logger.debug("done in %0.1f seconds" %telapsed)
        
    
    return ret
    

    
#*****************************************************************
# File manipulation/linking
#*****************************************************************
def link(pattern, dry_run=False):
    """ Processes a link specified in the format
    source --> dest, and creates links.
    
    'source' and 'dest' will be passed directly to a sytem call to ln -sf """
    logger=get_logger()
    arg = pattern
    cmd = 'ln -sf %s ' % arg
    logger.debug(cmd)
    subprocess.call(cmd, shell=True)

    
def copy(pattern, dry_run=False):
    logger = get_logger()
    cmd = 'cp %s ' % pattern
    logger.debug(cmd)
    if not dry_run:
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
    
    
def remove(pattern, dry_run=False):
    logger = get_logger()
    flist = glob.glob(pattern)
    for f in flist:
        if os.path.exists(f) and not dry_run:
            os.remove(f)    

def create(subdir, dry_run=False):                
    logger = get_logger()
    if not os.path.exists(subdir):
        logger.debug('creating directory %s ' % subdir)
        if not dry_run: 
            os.mkdir(subdir) 
                
                
                
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
    


def ordered_set(items):
    """create and ordered set from the iterable"""
    
    odict = OrderedDict([(item,None) for item in items])
    return list(odict.keys())

    

def get_time(base_time=None, delay=None, round=None):
    """ Returns base_time minus a delay in hours, rounded down to the nearest hour given in round.
    Warning - works by rounding back to the beginning of the day, and does not currently work for the 
    case where you request a cycle time which is later than the base_time
    
    Arguments:
        base_time  -- base time to calculate from
        delay  -- optional delay in hours to apply 
        round  -- a list of integer hours to restrict the return value to e.g. [0,6,12,18]"""
    
    logger = loghelper.get(LOGGER)

    hour  = datetime.timedelta(0, 60*60)

    base_time = base_time if base_time else datetime.datetime.today()
    
    delay = delay if delay else 0
    delayed_time  = base_time - delay * hour

    start = delayed_time
    if round:
        start_day   = datetime.datetime(delayed_time.year, delayed_time.month, delayed_time.day, 0, 0)           # throw away all time parts
        start_hour  = delayed_time.hour
        past_hours  = [ h for h in round if (h <= start_hour)]
        recent_hour = past_hours[-1]
        start       = start_day + recent_hour * hour
    

    return start

def read_times(tspec):    
    
    if isinstance(tspec, datetime.datetime):
        return [tspec]
    
    filename = tspec
    if not os.path.exists(filename):
        raise IOError("can not find file specifying initial times: %s " % init_file)

    with open(filename, 'r') as f:
        content = f.read().rstrip()

    init_strings = content.split('\n') 
    logger.debug(init_strings)
    # allow format often used by WRF, with an underscore seperating date and time
    init_strings = [s.replace('_', ' ') for s in init_strings]
    init_times = [ parser.parse(token) for token in init_strings]
    return init_times


    
def get_interval_times(start, freq, count, inclusive=False):    
    rec = rrule.rrule(freq, dtstart=start, count=count)
    return list(rec)


def get_bdy_times(init_time, fcst_hours, bdy_interval):
    """ Returns a list of datetime objects representing the times of boundary conditions.
    
    Read the init_time, fcst_hours and bdy_interval from config
    and returns a list of datetime objects representing the 
    boundary condition times. 
    
    Arguments:"""
    
    logger        = get_logger()
    hour          = datetime.timedelta(0, 60*60) 
    end_time      = init_time + datetime.timedelta(0, fcst_hours*60*60)
    
    if fcst_hours==0 or bdy_interval==0:
        return [init_time]
    #
    # Get the range of files representing boundary condition files
    # Because rrule is not inclusive, we add one hour on to the end 
    # time to make it so
    #                                                                  
    freq         = rrule.HOURLY
    rec          = rrule.rrule(freq, dtstart=init_time,until=end_time+hour, interval=bdy_interval)
    bdy_times    = list(rec)
    
    return bdy_times

def get_fcst_times(init_time, fcst_hours, history_interval):
    """ Return a list of datetimes representing forecast times 
    
    Arguments:
        init_time
        fcst_hours
        history_interval
    Returns:
    of datetime objects representing the forecast output times"""
    
    logger           = get_logger()
    logger.debug("get_fcst_times called")
    
    hour             = datetime.timedelta(0, 60*60)
    minute           = datetime.timedelta(0, 60) 
    end_time         = init_time + fcst_hours*hour
   
    freq          = rrule.MINUTELY
    rec           = rrule.rrule(freq, dtstart=init_time, until=end_time+minute, interval=history_interval)
    fcst_times    = list(rec)
    logger.debug("Forecast start: %s \t end: %s" %(fcst_times[0], fcst_times[-1]))
    return fcst_times

    
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

def get_sst_time(init_time, delay):
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
    
    

    
def _listify(element):
    """ Ensures elements are contained in a list """
    
    # either it is a list already, or it is None
    if type(element)==type([]) or element==None:
        return element
    
    else:
        return [element]
