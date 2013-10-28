""" 
Module wrftools
=====

Provides a selection of functions for pre-processing and
running a WRF forecast.  

Author: Sam Hawkins sam.hawkins@vattenfall.com

Assumed domains directory structure:

    /model_run_dir --> namelist.input file and other settings specific to that run
        /wrfout      --> netcdf output from WRF
        /wrfpost     --> grib output from UPP
        /tseries     --> time series extracted at points
        /plots       --> graphical output from NCL


A locations file controls which variables get written to out to time series
This should have the format:
# comments
location_id,name,lat,lon
LOC1, Location One,58.0,1.5
LOC2, Location Two,56.0,-2.5

Time series output files will be named according to:
domain/model_run/tseries/U_80_2006-11-30_00.csv 

TODO
* Change time series ncl code to write netcdf files -- done
* Change namelist reading code to strip trailing commas and remove trailing quotes -- done
* Summarise file transfers in logging output -- done

CHANGES

2013-08-30 Modified ungrib to support multiple  grib files in one run

2013-07-11 Added job scheduling/queing functionality

2013-06-19 Updated code to allow WRF to be run from any directory. Executables 
           and other required files will be linked in.

2013-02-04 Rationalised the movement to and from /longbackup, now uses rsync for
            flexibility

2012-12-10 Implemented a more aggressive cleanup to remove WPS leftover files


2012-09-13 Updated structure to support operational forecasting, using flag 
           operational=.true. get_cases still needs tidying up

2012-09-05 Uses PyNIO as interpolation, as cnvgrib was failing, meaning time-series
           could not be extracted.

2012-07-27 Added functionality for writing out time series, reading time series
           reading power curves, and converting wind speeds into powers

2012-07-19 Changed shell calls to use run_cmd in order to have enable dummy runs
           where commands are not executed.

2012-05-*  Updated point stat to make much more use of metadata in the output
           in order to facillitate better breakdown of stats when read into database

2012-03-30 Updated run_point_stat to write a more descriptive tag into the 
           'MODEL' field for use in statistical analysis

2012-03-05 Updated functions to operate on one domain only, reading value
           from config[dom], and putting looping structure outside. """

import os
import subprocess
import sys
import shutil
import re
import traceback
import math
import numpy as np
import glob
import time, datetime
from dateutil import rrule
from namelist import Namelist, read_namelist, add_cmd_args

import glob

from visualisation import *
from customexceptions import *
import logging

from tseries import extract_tseries, power, tseries_to_json, json_to_web
from queue import fill_template, qsub, qstat

LOGGER         = 'wrf_forecast'


#*****************************************************************
# Constants
#*****************************************************************
HOUR = datetime.timedelta(0, 60*60)                 


#*****************************************************************
# Logging
#*****************************************************************

def create_logger(config):
    """ Creates and returns logger instance called wrf_forecast.
    
    This allows a common logger instance to be used for all parts of forecast. 
    create_logger registers a file AND a console (screen) handler.  
    Settings are passed in via the config dictionary. The debug level specified by the 
    debug_level entry, and file output is is directed to domain_dir/forecast.log.
    
    Arguments:
    config -- a dictionary containing configuration settings
    
    """
    
    debug_level   = config['debug_level']
    domain_dir    = config['domain_dir']
    log_file      = config['log_file']
    logger        = logging.getLogger(LOGGER)
    numeric_level = getattr(logging, debug_level.upper(), None)


    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    #
    # Determines what messages get passed to the handlers
    #
    logger.setLevel(numeric_level)
    
    #
    # Log to the screen and to a file
    #
    fh = logging.FileHandler(log_file,mode='w')
    ch = logging.StreamHandler()
    fh.setLevel(numeric_level)
    ch.setLevel(numeric_level)

    formatter = logging.Formatter('%(levelname)s\t %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    if 'mailto' in config:
        from customloggers import BufferingSendmailHandler
        mailto  = config['mailto']
        subject = config['mail_subject']
        buffer  = config['mail_buffer']
        mail_level = getattr(logging, config['mail_level'].upper(), None)
        eh = BufferingSendmailHandler(mailto, subject, buffer)
    
        eh.setLevel(mail_level)
        eh.setFormatter(formatter)
        logger.addHandler(eh)
    logger.debug('logging object created')
    return logger


def get_logger():
    return logging.getLogger(LOGGER)    
    
    
#******************************************************************************
# Running shell commands
#******************************************************************************

def mpirun(cmd, num_procs, hostfile, run_level, cmd_timing=False):
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

    if hostfile=='None':
        cmd = 'mpirun -n %d %s' % (nprocs,  cmd)

    else:
        cmd = 'mpirun -n %d -hostfile %s %s' % (nprocs, hostfile, cmd)

    logger.debug(cmd)
    
    t0          = time.time()
    if run_level=='RUN':
        ret = subprocess.call(cmd, shell=True)        
   
    telapsed = time.time() - t0
    if cmd_timing:
        logger.debug("done in %0.1f seconds" %telapsed)

def run(cmd, run_level='RUN', timing=False):
    """Executes and logs a shell command. If config['run_level']=='DUMMY', then
    the command is logged but not executed."""
    
    logger = get_logger()
    
    t0          = time.time()
    logger.debug(cmd)
    
    #
    # Only execute command if run level is 'RUN', 
    # otherwise return a non-error 0. 
    #
    if run_level=='RUN':
        ret = subprocess.call(cmd, shell=True)
    else:
        ret = 0
    
    telapsed = time.time() - t0
    if timing:
        logger.debug("done in %0.1f seconds" %telapsed)
    
    return ret
        

def run_cmd(cmd, config):
    """Executes and logs a shell command. If config['run_level']=='DUMMY', then
    the command is logged but not executed."""
    
    logger = get_logger()
    
    run_level   = config['run_level']
    cmd_timing  = config['cmd_timing']
    t0          = time.time()
    logger.debug(cmd)
    
    #
    # Only execute command if run level is 'RUN', 
    # otherwise return a non-error 0. 
    #
    if run_level=='RUN':
        ret = subprocess.call(cmd, shell=True)
    else:
        ret = 0
    
    telapsed = time.time() - t0
    if cmd_timing:
        logger.debug("done in %0.1f seconds" %telapsed)
    
    return ret


def run_cmd_queue(cmd,config, run_from_dir, log_file):
    """ Run a command via the scheduler, and wait in loop until
    command is expected to finish.
    
    Arguments:
        @executable -- full path of the executable
        @config     -- all the other settings!
        @run_from_dir   -- directory to run from 
        @log_file       -- redirect to different log file"""
    
    logger          = get_logger()    

    run_level       = config['run_level']
    num_procs       = config['num_procs']
    job_template    = config['job_template']
    job_script      = config['job_script']
    queue_name      = config['queue_name']
    poll_interval   = config['poll_interval']
    max_job_time    = config['max_job_time']


    #
    # Either cmd, or cmd args other_stuff
    #
    parts = cmd.split()
    if len(parts)==0:
        executable = cmd
    else:
        executable = parts[0]

    exe = os.path.split(executable)[-1]
    

    if log_file:
        log = log_file
    else:
        log = exe

    try:
        if type(queue_name)==type({}):
            qname = queue_name[exe]
        else:
            qname = queue_name
    
        if type(num_procs)==type({}):
            nprocs = num_procs[exe]
        else:
            nprocs = num_procs
    
        if type(max_job_time)==type({}):
            mjt = max_job_time[exe]
        else:
            mjt = max_job_time
            
        if type(poll_interval)==type({}):
            pint = poll_interval[exe]        
        else:        
            pint = poll_interval

    except KeyError, e:
        tb = traceback.format_exc()
        raise ConfigError(tb)    
    
    if qname=='None':
        mpirun(cmd, config['num_procs'], config['host_file'], config['run_level'], config['cmd_timing']) 
        return
    
    attempts = mjt / pint
    
    logger.debug('Submitting %s to %d slots on %s, polling every %s minutes for %d attempts' %(exe, nprocs, qname, pint, attempts ))
    replacements = {'<executable>': executable,
                '<jobname>': exe,
                '<qname>'  : qname,
                '<nprocs>' : nprocs,
                '<logfile>': log}

    fill_template(job_template,job_script,replacements)
    os.chdir(run_from_dir)
    logger.debug(job_script)
    
    if run_level!='RUN':
        return


    job_id = qsub(job_script)
   
    for i in range(attempts):
        output = qstat(job_id)
        if output=='':
            logger.debug('no queue status for job, presume complete')
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

def transfer(flist, dest, mode='copy', debug_level='NONE'):
    """Transfers a list of files to a destination.
    
    Arguments:
        @flist       -- source files to be copied/moved
        @dest        -- destination directory
        @mode        -- copy (leave original) or move (delete original). Default 'copy'
        @debug_level -- what level to report sucess/failure to """
    logger = get_logger()
    logger.info(' *** TRANSFERRING %d FILES TO %s ***' %(len(flist), dest))
    
    n=0
    if type(flist)!=type([]):
        flist = [flist]
    
    for f in flist:
        fname = os.path.split(f)[1]
        dname = '%s/%s' % (dest, fname)
        logger.debug(dname)
        # bit dangerous, could delete then fail
        if os.path.exists(dname):
            os.remove(dname)

        shutil.copy2(f, dname)
        if debug_level=='DEBUG':
            logger.debug('copied %s ---------> %s' % (f, dname))
        elif debug_level=='INFO':
            logger.info('copied %s ---------> %s' % (f, dname))
        if mode=='move':
            os.remove(f)                        
        n+=1

    logger.info(' *** %d FILES TRANSFERRED ***' % n )

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
    
    
def compress(config):
    """Compresses netcdf files to netcdf4 format. Relies on 
    the NCO operator nccopy.  Will try and compress all output netcdf files
    associated with the current initial time, based on the standard WRF naming 
    convention.  If a simulation produces multiple wrfout files for an
    initial time (i.e. one file per day for three days), then only the first file
    will be compressed under the current configuration.
    
    nccopy does not support the -O overwrite flag, so we need to manually rename the files,
    and remove the originals on sucess"""
    
    logger=get_logger()
    logger.info("*** Compressing wrfout files ***")
    wrfout_dir = config['wrfout_dir']
    init_time  = config['init_time']
    max_dom    = config['max_dom']
    comp_level = config['compression_level']
    
    
    wrfout_files = ['%s/wrfout_d%02d_%s' %(wrfout_dir, d, init_time.strftime('%Y-%m-%d_%H:%M:%S')) for d in range(1,max_dom+1)]
    for f in wrfout_files:
        logger.debug("compressing %s" % f)
        if not os.path.exists(f):
            raise MissingFile("could not find %s" % f)
        tmp_name = f + '.tmp'
        cmd = 'nccopy -k4 -d %s %s %s' %(comp_level, f, tmp_name)
        run_cmd(cmd, config)
        if not os.path.exists(tmp_name):
            raise IOError("compression failed for %s" % f)
        
        os.remove('%s' %f)
        os.rename(f+'.tmp', f) 
    
    logger.info("*** Done compressing wrfout files ***")        

def add_metadata(nl):
    """ Adds metadata tags into the wrfout files. Expects there to be one 
    wrfout file per init_time. If there are more, they will not have metadata added."""

    logger = get_logger()
    logger.info("*** Adding metadata to wrfout files ***")

    config = nl.settings
    wrfout_dir = config['wrfout_dir']
    init_time  = config['init_time']
    max_dom    = config['max_dom']
    
    metadata = nl.sections['metadata']
    logger.debug(metadata)
    wrfout_files = ['%s/wrfout_d%02d_%s' %(wrfout_dir, d, init_time.strftime('%Y-%m-%d_%H:%M:%S')) for d in range(1,max_dom+1)]
    
    for f in wrfout_files:
        logger.debug("compressing %s" % f)
        if not os.path.exists(f):
            raise MissingFile("could not find %s" % f)
        
        # create attribute description for ncatted 
        # note that we make the attribute names uppercase for consistency with WRF output
        att_defs = ' '.join(['-a %s,global,c,c,"%s"' %(s.upper(), config[s]) for s in metadata])
        logger.debug(att_defs)
        cmd = 'ncatted -O -h %s %s' % (att_defs, f)
        logger.debug(cmd)
        run_cmd(cmd, config)
    
    
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
    if fail_mode=='EXIT':
        sys.exit()








#*****************************************************************
# Preparation
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


def prepare(config):
    """Removes files specified in pre_clean. Creates subdirectories specfied in create_dirs,
    links files specified in wrf_links into wrf_model_run_dir."""

   
    model_run_dir  = config['model_run_dir']
    wrf_dir        = config['wrf_dir']
    wrf_run_dir    = config['wrf_run_dir']
    links          = config['link']
    pre_clean      = config['pre_clean'] 
    subdirs        = config['create_dirs']

    logger           = get_logger()
    logger.info('*** PREPARING DIRECTORIES ***')
    logger.debug("check_directories called")
    if not os.path.exists(model_run_dir):
        os.makedirs(model_run_dir)
    
    fulldirs = [ model_run_dir+'/'+d for d in subdirs ]
    for d in fulldirs:
        if not os.path.exists(d):
            logger.debug('creating directory %s ' %d)
            os.mkdir(d) 
   
    for pattern in pre_clean:
        flist = glob.glob(pattern)
        for f in flist:
            if os.path.exists(f):
                logger.debug('removing file: %s' % f )
                os.remove(f)


    for pattern in links:
        link(pattern)
    logger.info('*** DONE PREPARE ***')


def link(pattern):
    """ Processes a link specified in the format
    source --> dest, and creates links.
    
    'source' and 'dest' will be passed directly to a sytem call to ln -sf """
    logger=get_logger()
    parts = pattern.split('-->')
    source = parts[0].strip()
    dest   = parts[1].strip()
    cmd = 'ln -sf %s %s' %(source, dest)
    logger.debug(cmd)
    subprocess.call(cmd, shell=True)



#*****************************************************************
# Date/time functions
#*****************************************************************

def sub_date(s, init_time=None, valid_time=None):
    """Substitues a date into a string following standard format codes.
    Syntax of original string s:
    i  -- initial time
    v  -- valid time
    %y -- 2-digit year
    %Y -- 4-digit year
    %m -- 2 digit month
    %d -- 2-digit day
    %H -- 2 digit hour
    %M -- 2-digit minute
    %S -- 2-digit second 
    
    Returns: string with codes expanded"""
    
    if init_time:
    
        yi  = str(init_time.year)[2:]
        Yi  = str(init_time.year)
        mi  = '%02d' % init_time.month
        di  = '%02d' % init_time.day
        Hi  = '%02d' % init_time.hour
        Mi  = '%02d' % init_time.minute
        Si  = '%02d' % init_time.second

        #s = s.replace('%iY', Yi).replace('%iy',yi).replace('%im',mi).replace('%id', di).replace('%iH', Hi).replace('%iM', Mi).replace('%iS', Si)

        s = s.replace('%iY', Yi)
        s = s.replace('%iy', yi)
        s = s.replace('%im', mi)
        s = s.replace('%id', di) 
        s = s.replace('%iH', Hi)
        s = s.replace('%iM', Mi)
        s = s.replace('%iS', Si)

    if valid_time:
        yv  = str(init_time.year)[2:]
        Yv  = str(init_time.year)
        mv  = '%02d' % valid_time.month
        dv  = '%02d' % valid_time.day
        Hv  = '%02d' % valid_time.hour
        Mv  = '%02d' % valid_time.minute
        Sv  = '%02d' % valid_time.second
        
        s = s.replace('%vY', Yv)
        s = s.replace('%vy',yv)
        s = s.replace('%vm',mv)
        s = s.replace('%vd', dv) 
        s = s.replace('%vH', Hv)
        s = s.replace('%vM', Mv)
        s = s.replace('%vS', Sv)

    if init_time and valid_time:
        delta = valid_time - init_time
        fhr   = delta.days * 24 + int(delta.seconds / (60*60))
        fH    = '%02d' % fhr
        s = s.replace('%fH', fH)
    
    return s



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
    logger.debug("get_operational_init_times called")


    fcst_hours    = config['fcst_hours']
    operational   = config['operational']
    cycles        = config['cycles']
    gm_delay      = config['gm_delay']
    
   
        
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
    logger.debug("getting most recent operational case: %s" % start)
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
    logger.debug("get_init_times called")
    
    operational   = config['operational']
    start         = config['start']
    end           = config['end']
    init_interval = config['init_interval']
    freq          = rrule.HOURLY
    
    if operational:
        start = get_operational_init_time(config)
        end = start
        logger.debug('got init_time %s' % start)
    if type(start)!=type([]):
        start= [start]
    if type(end)!=type([]):
        end = [end]


    if len(start)!=len(end):
        raise IOError('differenr start and end times specified')

    init_times = []
    
    for s, e in zip(start, end):
        rec           = rrule.rrule(freq, dtstart=s, until=e, interval=init_interval)
        init_times.extend(list(rec))

    logger.debug("got the following initial times: ")
    for t in init_times:
        logger.debug("%s" %t)
    
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
    return filelist
    

    
#*****************************************************************
# Comopnent run functions
#*****************************************************************
    
    

def run_gribmaster(config):
    """Runs the gribmaster programme to download the most recent boundary conditions """
    logger      = get_logger()
    gm_dir      = config['gm_dir']
    gm_transfer = config['gm_transfer']
    gm_dataset  = config['gm_dataset']
    start       = config['init_time']
    fcst_hours  = config['fcst_hours']
    gm_log      = config['gm_log']
    gm_sleep    = config['gm_sleep'] # this is in minutes
    gm_max_attempts = int(config['gm_max_attempts'])

    log_dir = '/home/slha/forecasting'
       
    cmd     = '%s/gribmaster --verbose --%s --dset %s --date %s --cycle %s --length %s > %s' %(gm_dir, gm_transfer, gm_dataset, start.strftime('%Y%m%d'), start.strftime('%H'), fcst_hours, gm_log )

    for attempt in range(gm_max_attempts):
        logger.info('*** RUNNING GRIBMASTER, %s attempt ***' % (attempt+1))
        run_cmd(cmd, config)
        
        cmd = 'grep "BUMMER" %s' % gm_log # check for failure
        ret = subprocess.call(cmd, shell=True)
        # if we positively find the string BUMMER, we know we have failed
        if ret==0:
            logger.error('*** FAIL GRIBMASTER: Attempt %d of %d ***' % (attempt+1, gm_max_attempts))
            logger.info('Sleeping for %s seconds' % gm_sleep) 
            time.sleep(gm_sleep*60)
        
        # else we check for definite sucess
        else:
            cmd = 'grep "ENJOY" %s' % gm_log # check for failure
            ret = subprocess.call(cmd, shell=True)
            if ret==0:
                logger.info('*** SUCESS GRIBMASTER ***')
                return
        
        
    raise IOError('gribmaster did not find files after %d attempts' % gm_max_attempts)




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

def get_sst(config):
    """ Downloads SST fields from an ftp server.
    Whoever is running this must have the http_proxy environment variable set
    correctly to allow them to download files through the proxy.  Example:
    http_proxy = http://slha:password@webproxy-se.corp.vattenfall.com:8080"""
    logger      = get_logger()
    # create an lftpscript in model run dir
    
    logger.info('*** FETCHING SST ***')
    domain_dir    = config['domain_dir']
    model_run     = config['model_run']
    tmp_dir        = config['tmp_dir']
    http_proxy     = os.environ['http_proxy']
    home           = os.environ['HOME']
    sst_server     = config['sst_server']
    sst_server_dir = config['sst_server_dir']
    sst_local_dir  = config['sst_local_dir']
    sst_time       = get_sst_time(config)
    sst_filename   = get_sst_filename(config)
   
    if not os.path.exists(sst_local_dir):
        os.makedirs(sst_local_dir)
    
    if os.path.exists('%s/%s' %(sst_local_dir, sst_filename)):
        logger.info('*** SST ALREADY EXISTS LOCALLY, NOT DOWNLOADED ***')
        return
    lftpfilename = '%s/%s/lftpscript' % (domain_dir, model_run)
    logger.debug('Writing lftpscript to %s' % lftpfilename)
    lftpscript     = open(lftpfilename, 'w')    
    lftpscript.write('lcd %s\n' % sst_local_dir)    
    lftpscript.write('set ftp:proxy %s\n' % http_proxy) 
    lftpscript.write('set hftp:use-type no\n')
    lftpscript.write('open %s\n' % sst_server)
    lftpscript.write('get %s/%s\n' % (sst_server_dir,sst_filename))
    lftpscript.write('bye')
    lftpscript.close()
    
    cmd = '/usr/bin/lftp -f %s' % lftpfilename
    run_cmd(cmd, config)
    # check if file downloaded

    if not os.path.exists('%s/%s' %(sst_local_dir, sst_filename)):
        raise IOError('SST file: %s not downloaded' % sst_filename)
    logger.info('*** SUCCESS SST DOWNLOADED ***')



def ungrib_sst(config):
    """ Runs ungrib.exe for SST fields, makes and modifies a copy of namelist.wps,
    then restores the original namelist.wps"""
    logger = get_logger()
    
    wps_dir      = config['wps_dir']
    wps_run_dir  = config['wps_run_dir']
    tmp_dir      = config['tmp_dir']
    domain_dir   = config['domain_dir']
    model_run    = config['model_run']
    model_run_dir = config['model_run_dir']
    init_time    = config['init_time']
    max_dom      = config['max_dom']
    sst_local_dir = config['sst_local_dir']
    sst_time     = get_sst_time(config)
    sst_filename = get_sst_filename(config)
    vtable_sst   = wps_dir+'/ungrib/Variable_Tables/'+config['sst_vtable']
    vtable_dom   = wps_dir+'/ungrib/Variable_Tables/'+config['vtable']
    vtable       = wps_run_dir+'/Vtable'
    queue        = config['queue']
    log_file     = '%s/ungrib.sst.log' % wps_run_dir
    namelist_wps  = wps_run_dir+'/namelist.wps'
    namelist_dom  = '%s/namelist.wps' % model_run_dir
    namelist_sst  = '%s/namelist.sst' % model_run_dir
    namelist      = read_namelist(namelist_dom)

    #
    # update one line to point to the new SST field
    # ungrib.exe will name SST field as e.g.
    # SST:2013-04-24_00
    #
    constants_name = '%s/SST:%s' %(wps_run_dir, sst_time.strftime('%Y-%m-%d_%H'))
    logger.debug('Updating constants_name ----> %s' % constants_name)
    namelist.update('constants_name', constants_name, section='metgrid')

    # Write the changes into the original namelist file
    namelist.to_file(namelist_dom)

    #
    # Update start and end time to process SST
    #
    start_str  = sst_time.strftime("%Y-%m-%d_%H:%M:%S")
    end_str    = sst_time.strftime("%Y-%m-%d_%H:%M:%S")
    logger.debug("Updating namelist.sst")
    logger.debug('PREFIX ------> SST')
    logger.debug('start_date---> ' +start_str)
    logger.debug('end_date-----> '+ end_str)

    namelist.update('prefix', 'SST')
    namelist.update('start_date', [start_str]*max_dom)
    namelist.update('end_date',   [end_str]*max_dom)
    logger.debug('writing modified namelist.sst to file -------> %s' % namelist_sst)
    namelist.to_file(namelist_sst)

    #remove any linked namelist.wps 
    logger.debug('removing namelist.wps')
    if os.path.exists(namelist_wps): 
        os.remove(namelist_wps)

    # link namelist.sst to namelist.wps in WPS run dir
    logger.debug('linking namelist.sst -----> namelist.wps')
    cmd = 'ln -sf %s %s' %(namelist_sst, namelist_wps)
    run_cmd(cmd, config)

    logger.debug('removing Vtable')
    if os.path.exists(vtable):
        os.remove(vtable)
    logger.debug('linking Vtable.SST ----> Vtable')
    cmd = 'ln -sf %s %s' %(vtable_sst, vtable)
    run_cmd(cmd, config)

    # run link_grib to link SST gribs files
    logger.debug('Linking SST GRIB files')
    cmd = '%s/link_grib.csh %s/%s' %(wps_dir, sst_local_dir, sst_filename)
    run_cmd(cmd, config)


    logger.info('*** RUNNING UNGRIB FOR SST ***')
    cmd     =  '%s/ungrib.exe' % wps_run_dir
    if queue:
        run_cmd_queue(cmd, config, wps_run_dir,log_file )
    else:
        mpirun(cmd, config['num_procs'], config['host_file'], config['run_level'], config['cmd_timing']) 


    cmd = 'grep "Successful completion" ./ungrib.log*' # check for success
    ret = run_cmd(cmd, config)
    if ret!=0:
        raise IOError('Ungrib failed for SST')
    
    logger.info('*** SUCCESS UNGRIB SST ***')
    logger.debug('Removing namelist.wps')
    if os.path.exists(namelist_wps): 
        os.remove(namelist_wps)
    # link in original (unmodified) namelist.wps
    cmd = 'ln -sf %s %s' %(namelist_dom, namelist_wps)    
    run_cmd(cmd, config)


def link_namelist_wps(config):
    """Links namelist_wps into wps_run_dir"""    
    
    logger = get_logger()
    #
    # link namelist.wps file from domain dir to 
    # wps dir. Fist check it exists
    #
    namelist_wps = config['namelist_wps']
    namelist_run = '%s/namelist.wps' % config['wps_run_dir']
    
    #
    # Check if namelist exists in model_run_dir directory
    #    
    if not os.path.exists(namelist_wps):
        raise IOError('could not find namelist.wps file: %s' % namelist_wps)
        
    if os.path.exists(namelist_run):
        logger.debug('removing existing namelist.wps file: %s' % namelist_run)
        os.remove(namelist_run)
    
    #
    # Execute this command even in a dummy run, so that namelist file is linked
    # correctly and can be updated by other commands
    #
    cmd = 'ln -sf %s %s ' %(namelist_wps, namelist_run)
    logger.debug(cmd)
    subprocess.call(cmd, shell=True)
        
    

    
def prepare_wps(config):
    """ Runs all the pre-processing steps necessary for running WPS.
    
    Reads the current value of init_time from config, and links 
    boundary condition files into correct directory. Creates an output
    directory for the met_em files.
    
    Arguments:
    config -- dictionary containing various configuration options"""
    
    logger       = get_logger()
    logger.debug('*** PREPARING FILES FOR WPS ***')
    
    wps_dir       = config['wps_dir']          # the base installation of WPS
    wps_run_dir   = config['wps_run_dir']      # the directory to run WPS from
    model_run_dir = config['model_run_dir']    # model run directory 
    met_em_dir    = config['met_em_dir']
    init_time     = config['init_time']

    
    grb_input_fmt = config['grb_input_fmt']
    vtable        = config['vtable']
    bdy_times     = get_bdy_times(config)

    if type(grb_input_fmt)==type({}):
        logger.debug(grb_input_fmt)
        fmts = grb_input_fmt.values()
        
    else:
        fmts = [grb_input_fmt]
    
    
    for fmt in fmts:
        #
        # Generate filelist based on the initial time, and the forecast hour
        #        
        filelist = get_bdy_filenames(fmt, bdy_times)

        #
        # Check the boundary files exist
        #
        logger.debug('checking boundary condition files exists')    
        for f in filelist:
            if not os.path.exists(f):
                raise IOError('cannot find file: %s' %f)
        
    logger.debug('all boundary conditions files exist')
    
    #
    # Run the link_grib scipt to link the FNL files
    #
    logger.debug('running link_grib.csh script to link grib files to GRIBFILE.AAA etc')
    os.chdir(wps_run_dir)
    args = ' '.join(filelist)
    cmd = '%s/link_grib.csh %s' %(wps_run_dir,args)
    run_cmd(cmd, config)

    logger.debug('Path for met_em files is %s' % met_em_dir)
    if not os.path.exists(met_em_dir):
        os.makedirs(met_em_dir)

   
    logger.debug('*** FINISHED PREPARING FILES FOR WPS ***')    
    return 0




def update_namelist_wps(config):
    """ Updates the namelist.wps to reflect updated settings in config
    
    Arguments:
    config -- dictionary containing various configuration options
        
    """    
    logger     = get_logger()
    logger.debug('*** UPDATING namelist.wps ***')

    #domain_dir = config['domain_dir']
    #model_run  = config['model_run']
    #wps_dir    = config['wps_dir']
    wps_run_dir= config['wps_run_dir']          # required for opt_geogrid_tbl_path
    #bdy_conditions = config['bdy_conditions'] 
    
    namelist_wps = config['namelist_wps']
    shutil.copyfile(namelist_wps, namelist_wps+'.backup')
    
    bdy_times  = get_bdy_times(config)
    
    max_dom    = config['max_dom']
    init_time  = config['init_time']

    met_em_dir = sub_date(config['met_em_dir'], init_time=init_time)
    geo_em_dir = config['geo_em_dir']

    bdy_interval = config['bdy_interval']
    interval_seconds = bdy_interval * 60 * 60

    logger.debug('reading namelist.wps <--------- %s' % namelist_wps)
    namelist = read_namelist(namelist_wps)

    #
    # Update some options based on the forecast config file
    #
    namelist.update('max_dom', max_dom)
    namelist.update('opt_output_from_geogrid_path', geo_em_dir, section='share')
    namelist.update('opt_geogrid_tbl_path', wps_run_dir, section='geogrid')
    namelist.update('opt_metgrid_tbl_path', wps_run_dir, section='metgrid')
    namelist.update('interval_seconds', [interval_seconds])
    
    #
    # Generate formatted strings for inclusion in the namelist.wps file
    #
    start_str  = bdy_times[0].strftime("%Y-%m-%d_%H:%M:%S")
    end_str    = bdy_times[-1].strftime("%Y-%m-%d_%H:%M:%S")
    logger.debug("Updating namelist.wps start and end")
    logger.debug(start_str)
    logger.debug(end_str)

    namelist.update('start_date', [start_str]*max_dom)
    namelist.update('end_date',   [end_str]*max_dom)

        
    logger.debug('writing modified namelist.wps to file')
    namelist.to_file(namelist_wps)
    logger.debug('*** FINISHED UPDATING namelist.wps ***')



def prepare_ndown(config):
    """Runs a one-way nested simulation using ndown.exe
    We assume the coarse resolution run has been done, 
    and we have wrfout_d01.date files.
    
    We only need to run metgrid for the initial forecast time.
    
    We have two options, either we force the user to do all the renaming themselves, 
    or we allow them to utilise the original namelist.input file, and add effectivley
    add a column onto that. This could be done via a bunch of smaller utility steps.
    e.g. shift_namelist namelist.input 3 > namelist.input
    
    Which would rotate the columns of a namelist.input file so that the n-th column 
    becomes the first column.
    
        
    Therefore we have to run ungrib, geogrid, metgrid
    Assume the geo_em files exist for both domains.
    What """

    logger = get_logger()
    logger.info('*** PREPARING NDOWN ***')
    namelist_wps   = config['namelist_wps']
    namelist_input = config['namelist_input']
    max_dom        = config['max_dom']
    wrf_run_dir    = config['wrf_run_dir']
    
    
    if max_dom!=2:
        raise ConfigError("max_dom must equal 2 when doing ndown runs")
    
    bdy_times = get_bdy_times(config)
    ndown_fmt = config['ndown_fmt']
    
    wrfout_d01_files = [sub_date(ndown_fmt, init_time=bdy_times[0], valid_time=t) for t in bdy_times]
    for f in wrfout_d01_files:
        if not os.path.exists(f):
            raise MissingFile("File: %s missing" % f)
        cmd = 'ln -sf %s %s' % (f, wrf_run_dir)
        run_cmd(cmd, config)
    
    
    # Check for wrfinput_d02
    wrfinput_d02 = '%s/wrfinput_d02' % wrf_run_dir
    if not os.path.exists(wrfinput_d02):
        raise MissingFile("wrfinput_d02 is missing")
    
    os.rename('%s/wrfinput_d02' % wrf_run_dir, '%s/wrfndi_d02' % wrf_run_dir)
    
    
    namelist         = read_namelist(namelist_input)
    
    # History interval is in minutes
    history_interval = namelist.settings['history_interval']
    interval_seconds = history_interval[0] * 60
    namelist.update('interval_seconds', interval_seconds)
    namelist.insert('io_form_auxinput2', 2, 'time_control')
    namelist.to_file(namelist_input)
    
    logger.info('*** DONE PREPARE NDOWN ***')
    
def run_ndown(config):
    logger = get_logger()
    logger.info('*** RUNNING NDOWN ***')
    
    wrf_run_dir = config['wrf_run_dir']
    queue       = config['queue']
    log_file    = '%s/ndown.log' % wrf_run_dir
    
    cmd = '%s/ndown.exe' % wrf_run_dir
    
    nprocs = config['num_procs']
    poll_interval = config['poll_interval']
    logger.debug(poll_interval)
    logger.debug(nprocs)
    logger.debug(nprocs['ndown.exe'])
    
    if queue:
        run_cmd_queue(cmd, config, wrf_run_dir, log_file)
        
    else:
        mpirun(cmd, nprocs, config['host_file'], config['run_level'], config['cmd_timing'])


    cmd = 'grep "Successful completion" %s' % log_file # check for success
    ret = run_cmd(cmd,config)
    if ret!=0:
        raise IOError('ndown.exe did not complete')
    
    logger.info('*** SUCESS NDOWN ***')

    
    
    
    
def run_ungrib(config):
    """ Runs ungrib.exe and checks output was sucessfull
    If vtable and gbr_input_fmt are NOT dictionaries, 
    then dictionarius will be constructed from them using 
    the key bdy_conditions from the metadata
    
    Arguments:
    config -- dictionary specifying configuration options
    
    """
    logger        = get_logger()
    queue         = config['queue']
    wps_dir       = config['wps_dir']
    wps_run_dir   = config['wps_run_dir']
    namelist_wps  = config['namelist_wps']
    model_run_dir = config['model_run_dir']    # model run directory 
    met_em_dir    = config['met_em_dir']
    init_time     = config['init_time']
    log_file      = '%s/ungrib.log' % wps_run_dir
    vtable        = config['vtable']
    grb_input_fmt = config['grb_input_fmt']
    bdy_conditions = config['bdy_conditions']
    
    logger.info("*** RUNNING UNGRIB ***")
    
    namelist = read_namelist(namelist_wps)
    
    bdy_times     = get_bdy_times(config)
    

    if type(grb_input_fmt)!=type({}):
        grb_input_fmt = {bdy_conditions:grb_input_fmt}

    if type(vtable)!=type({}):
        vtable = {bdy_conditions:vtable}


    #
    # Check that boundary conditions exist
    #     
    for key in vtable.keys():
        
        fmt = grb_input_fmt[key]
        #
        # Generate filelist based on the initial time, and the forecast hour
        #        
        filelist = get_bdy_filenames(fmt, bdy_times)

        #
        # Check the boundary files exist
        #
        logger.debug('checking boundary condition files exists')    
        for f in filelist:
            if not os.path.exists(f):
                raise IOError('cannot find file: %s' %f)
        
    
    
    logger.debug('all boundary conditions files exist')
    
    for key in vtable.keys():
        fmt = grb_input_fmt[key]
        filelist = get_bdy_filenames(fmt, bdy_times)
        logger.debug('running link_grib.csh script to link grib files to GRIBFILE.AAA etc')
        os.chdir(wps_run_dir)
        args = ' '.join(filelist)
        cmd = '%s/link_grib.csh %s' %(wps_run_dir,args)
        run_cmd(cmd, config)
  
        vtabname = vtable[key]
        prefix = key
        namelist.update('prefix', key)
        namelist.to_file(namelist_wps)
        link_namelist_wps(config)
        vtab_path = wps_dir+'/ungrib/Variable_Tables/'+vtabname
        vtab_wps  = wps_run_dir+'/Vtable'

        if os.path.exists(vtab_wps):
            os.remove(vtab_wps)
        cmd = 'ln -sf %s %s' %(vtab_path, vtab_wps)
        logger.debug(cmd)
        subprocess.call(cmd, shell=True)    

        cmd     =  '%s/ungrib.exe' % wps_run_dir
        
        if queue:
            run_cmd_queue(cmd, config, wps_run_dir, log_file)
        
        else:
            mpirun(cmd, config['num_procs'], config['host_file'], config['run_level'], config['cmd_timing'])


        cmd = 'grep "Successful completion" %s/ungrib.log*' % wps_run_dir # check for success
        ret = run_cmd(cmd,config)
        if ret!=0:
            raise IOError('ungrib.exe did not complete')
    
    logger.info('*** SUCESS UNGRIB ***')

def run_geogrid(config):
    """ Runs geogrid.exe and checks output was sucessful
    
    Arguments:
    config -- dictionary specifying configuration options
    
    """
    logger = get_logger()
    logger.info("*** RUNINING GEOGRID ***")
    wps_run_dir    = config['wps_run_dir']
    domain_dir     = config['domain_dir']
    queue          = config['queue']
    log_file       = '%s/geogrid.log' % wps_run_dir
    
    geogrid_wps = '%(wps_run_dir)s/GEOGRID.TBL' % config

    if not os.path.exists(geogrid_wps):
        raise IOError("Could not find GEOGRID.TBL at: %s " % geogrid_wps)
    

    cmd       =  '%s/geogrid.exe' % wps_run_dir
    
    if queue:        
        run_cmd_queue(cmd, config, wps_run_dir, log_file)
    
    else:
        mpirun(cmd, config['num_procs'], config['host_file'], config['run_level'], config['cmd_timing'])

    
    cmd = 'grep "Successful completion" %s/geogrid.log*' %(wps_run_dir)
    ret = run_cmd(cmd, config)
    if ret!=0:
        raise IOError('geogrid.exe did not complete')

    logger.info('*** SUCESS GEOGRID ***')

def run_metgrid(config):
    """ Runs metgrid.exe and checks output was sucessful
    
    Arguments:
    config -- dictionary specifying configuration options
    
    """
    logger = get_logger()
    logger.info("*** RUNNING METGRID ***")
    
    queue          = config['queue']
    wps_run_dir    = config['wps_run_dir']
    log_file       = '%s/metgrid.log' % wps_run_dir
    bdy_conditions = config['bdy_conditions']
    namelist_wps   = config['namelist_wps']
    namelist       = read_namelist(namelist_wps)
    
    met_em_dir     = sub_date(config['met_em_dir'], config['init_time'])        
    
    #
    # vtable may be a dictionary to support running ungrib multiple
    # times. In which case, we need to put multiple prefixes into
    # the namelist.wps file
    #
    
    vtable = config['vtable']
    
    if type(vtable)==type({}):
        prefixes = vtable.keys()
    else:
        prefixes = [bdy_conditions]    

        
    namelist.update('fg_name', prefixes)
    namelist.update('opt_output_from_metgrid_path', met_em_dir, section='metgrid')
    if not 'constants_name' in config.keys():
        namelist.remove('constants_name')
        
    namelist.to_file(namelist_wps)
    
    logger.debug('met_em_dir: %s' % met_em_dir)
    if not os.path.exists(met_em_dir):
        logger.debug('creating met_em_dir: %s ' % met_em_dir)
        os.makedirs(met_em_dir)

    os.chdir(wps_run_dir)
    cmd      =  "%s/metgrid.exe" % wps_run_dir
    
    if queue:
        run_cmd_queue(cmd, config, wps_run_dir, log_file)
    
    else:
        mpirun(cmd, config['num_procs'], config['host_file'], config['run_level'], config['cmd_timing'])


    cmd = 'grep "Successful completion" %s/metgrid.log*' % wps_run_dir
    ret = run_cmd(cmd, config)
    if ret!=0:
        raise IOError('metgrid.exe did not complete')
    
    logger.info('*** SUCESS METGRID ***')


def prepare_wrf(config):
    """Checks that met_em files exist, and links into WRF/run directory. 
    
    Arguments:
    config -- a dictionary containing forecast options

    """
    logger = get_logger()    
    logger.debug('*** PREPARING FILES FOR WRF ***')
    
    met_em_format      = "%Y-%m-%d_%H:%M:%S"
    domain_dir   = config['domain_dir']
    
    wrf_run_dir  = config['wrf_run_dir']
    model_run_dir  = config['model_run_dir']
    max_dom      = config['max_dom']
    domains      = range(1,max_dom+1)
    init_time    = config['init_time']
    fcst_hours   = config['fcst_hours']
    bdy_interval = config['bdy_interval']
    bdy_times    = get_bdy_times(config)
    met_em_dir   = sub_date(config['met_em_dir'], init_time=init_time)
    met_em_files = ['%s/met_em.d%02d.%s.nc' % (met_em_dir,d, t.strftime(met_em_format)) for d in domains for t in bdy_times] 
    namelist_run    = '%s/namelist.input' % wrf_run_dir
    namelist_input = config['namelist_input']
    
    
    logger.debug('linking met_em files:')
    
    #
    # Link met_em files. There are two options for error handling here.
    # The first is to abort if any of the met_em files are missing.
    # The second is just to run wrf and see how far it gets before
    # running out of files. This will allow a partial forecast to run, 
    # even if later files are missing.
    #    
    # To use the first approach, raise an exception when a missing
    # file is encountered, otherwise just print a warning message.
    #
    # Actually, the two are equivalent so long as the met_em files 
    # are sorted.
    #
    for f in met_em_files:
        if not os.path.exists(f):
            raise IOError('met_em file missing : %s' %f)
        cmd = 'ln -sf %s %s/'%(f, wrf_run_dir)
        run_cmd(cmd, config)
    
    
    logger.debug('linking namelist.input to wrf_run_dir')
    cmd = 'rm -f %s' % namelist_run
    run_cmd(cmd, config)
    cmd = 'ln -sf %s %s' %(namelist_input, namelist_run)
    run_cmd(cmd, config)

    logger.debug('*** FINISHED PREPARING FILES FOR WRF ***')




def update_namelist_input(config):    
    """ Updates the namelist.input file to reflect updated settings in config.
    Adds a non-standard &metadata section to give a name to the model run
    
    Arguments:
    config -- dictionary containing various configuration options
        
    """        
    logger = get_logger()        
    logger.debug('*** UPDATING namelist.input ***')
    
    domain_dir    = config['domain_dir']
    wrf_dir       = config['wrf_dir']
    model         = config['model']
    model_run     = config['model_run']
    model_run_dir = config['model_run_dir']
    domain        = config['domain']
        
    namelist_run  = '%s/namelist.input'  % model_run_dir
    namelist_input = config['namelist_input']
    namelist_wps   = config['namelist_wps']
    shutil.copyfile(namelist_input, namelist_input+'.backup')
    
    # read settings from domain-based namelist
    namelist        = read_namelist(namelist_input)   

    # read settings from domain-based namelist.wps
    namelist_wps   = read_namelist(namelist_wps)   
    wps_settings   = namelist_wps.settings


    #
    # Add new metadata section to namelist.input
    #
    logger.debug('Adding metatdata to the namelist.input')
    logger.debug('domain = %s'    %domain)
    logger.debug('model = %s'     %model)
    logger.debug('model_run = %s' %model_run)
    namelist.update('domain', domain, 'metadata')
    namelist.update('model',model, 'metadata')
    namelist.update('model_run',model_run, 'metadata')  

    
    #
    # Overule max_dom with one in config
    #
    max_dom = config['max_dom']
    namelist.update('max_dom', max_dom)
    #logger.debug("Syncing dx and dy between namelist.wps and namelist.input")
    #dx = wps_settings['dx']
    #dy = wps_settings['dy']
    #logger.debug("namleist.wps: dx: %s ------> namelist.input" % dx)
    #logger.debug("namleist.wps: dy: %s ------> namelist.input" % dy)
    #namelist.update('dx', wps_settings['dx'])
    #namelist.update('dy', wps_settings['dy'])    
    fcst_hours       = config['fcst_hours']
    fcst_times       = get_fcst_times(config)
    history_interval = config['history_interval']   
    bdy_interval     = config['bdy_interval']  # this is in hours         
    
    interval_seconds = 60*60*bdy_interval
    
    start   = fcst_times[0]
    end     = fcst_times[-1]
    diff    = end - start
    
    
    #
    # I'm still not sure how the WRF namelist works between 
    # the start and end settings and the run_XX settings.
    # I think we can just keep days as zero, and work entirely
    # in hours
    #
    namelist.update('start_year', [start.year] * max_dom)
    namelist.update('start_month',[start.month]* max_dom)
    namelist.update('start_day',  [start.day]  * max_dom)
    namelist.update('start_hour', [start.hour] * max_dom)
    namelist.update('end_year',   [end.year]   * max_dom)
    namelist.update('end_month',  [end.month]  * max_dom)
    namelist.update('end_day',    [end.day]    * max_dom)
    namelist.update('end_hour',   [end.hour]   * max_dom)
    namelist.update('run_days',   [0])   
    namelist.update('run_hours',  [fcst_hours] )   
    #namelist.update('run_minutes',[0])   
    namelist.update('history_interval', [history_interval] * max_dom)
    namelist.update('interval_seconds', [interval_seconds])


    #
    # If DFI is being used, update DFI settings
    # From user guide:
    # "For time specification, it typically needs to integrate 
    # backward for 0.5 to 1 hour, and integrate forward for half of the time."
    #
    # should we just write this everytime into the file and rely of dfi_opt 
    # as the on/off switch?
    #
    hour         = datetime.timedelta(0, 60*60)
    minute       = datetime.timedelta(0, 60)
    #dfi_bck      = config['dfi_bck'] * minute
    #dfi_fwd      = config['dfi_fwd'] * minute
    #dfi_bckstop  = start - dfi_bck
    #dfi_fwdstop  = start + dfi_fwd
    

    #namelist.update('dfi_bckstop_year',   dfi_bckstop.year,   'dfi_control')
    #namelist.update('dfi_bckstop_month',  dfi_bckstop.month,  'dfi_control')
    #namelist.update('dfi_bckstop_day',    dfi_bckstop.day,    'dfi_control')
    #namelist.update('dfi_bckstop_hour',   dfi_bckstop.hour,   'dfi_control')
    #namelist.update('dfi_bckstop_minute', dfi_bckstop.minute, 'dfi_control')
    #namelist.update('dfi_bckstop_second', dfi_bckstop.second, 'dfi_control')
    #namelist.update('dfi_fwdstop_year',   dfi_fwdstop.year,   'dfi_control')
    #namelist.update('dfi_fwdstop_month',  dfi_fwdstop.month,  'dfi_control')
    #namelist.update('dfi_fwdstop_day',    dfi_fwdstop.day,    'dfi_control')
    #namelist.update('dfi_fwdstop_hour',   dfi_fwdstop.hour,   'dfi_control')
    #namelist.update('dfi_fwdstop_minute', dfi_fwdstop.minute, 'dfi_control')
    #namelist.update('dfi_fwdstop_second', dfi_fwdstop.second, 'dfi_control')
   
    logger.debug('writing new settings to file')
    namelist.to_file(namelist_input)
    
    #logger.debug(namelist)
    logger.debug('*** FINISHED UPDATING namelist.input ***')  

    
def run_real(config):
    """ Run real.exe and check output was sucessful
    Arguments:
    config -- dictionary containing various configuration options """
    
    logger = get_logger()    
    logger.info('*** RUNNING REAL ***')
    
    queue           = config['queue']
    model_run_dir   = config['model_run_dir']
    wrf_run_dir     = config['wrf_run_dir']
    wps_dir         = config['wps_dir']
    domain          = config['domain']
    model_run       = config['model_run']
    init_time       = config['init_time']
    log_file        = '%s/real.log' % wrf_run_dir


    # Log files from real appear in the current directory, 
    # so we need to change directory first.
    os.chdir(wrf_run_dir)
    cmd     =  "%s/real.exe" % wrf_run_dir
    if queue:
        run_cmd_queue(cmd, config, wrf_run_dir, log_file)
    else:
        mpirun(cmd, 1, config['host_file'], config['run_level'], config['cmd_timing'])
    
    
    rsl = '%s/rsl.error.0000' % wrf_run_dir
    if not os.path.exists(rsl):
        raise IOError('No log file found for real.exe')

    # now copy rsl file to a log directory
    cmd = 'cp %s %s/rsl/rsl.error.%s.%s.%s' % (rsl, model_run_dir, domain, model_run, init_time.strftime('%y-%m-%d_%H') )
    run_cmd(cmd, config)



    cmd = 'grep "SUCCESS COMPLETE" %s/rsl.error.0000' % wrf_run_dir
    ret = run_cmd(cmd, config)
    
    if ret!=0:
        raise IOError('real.exe did not complete')


    logger.info('*** SUCESS REAL ***')


 
def run_wrf(config):
    """ Run wrf.exe and check output was sucessful
    
    Arguments:
    config -- dictionary containing various configuration options
    
    """
    logger          = get_logger()    
    logger.info('*** RUNNNING WRF ***')
    queue         = config['queue']
    wrf_run_dir   = config['wrf_run_dir']
    log_file      = '%s/wrf.log' % wrf_run_dir
    
    executable  = '%s/wrf.exe' % wrf_run_dir
    if queue:
        run_cmd_queue(executable, config, wrf_run_dir, log_file)
    
    else:
        mpirun(executable, config['num_procs'], config['host_file'], config['run_level'], config['cmd_timing'])

    #
    # Check for success
    #    
    cmd = 'grep "SUCCESS COMPLETE" %s/rsl.error.0000' % wrf_run_dir
    ret =  run_cmd(cmd, config)
    if ret!=0:
        raise IOError('wrf.exe did not complete')
    
    logger.info('*** SUCESS WRF ***')


def move_wrfout_files(config):
    """ Moves output files from run directory to wrfout 
    director"""
    logger = get_logger()    
    logger.info('*** MOVING WRFOUT FILES AND NAMELIST SETTINGS ***')
    
    domain        = config['domain']
    model_run     = config['model_run']
    model_run_dir = config['model_run_dir']
    wrf_run_dir   = config['wrf_run_dir']
    init_time     = config['init_time']
    init_str      = init_time.strftime('%Y-%m-%d_%H')

    namelist_input = config['namelist_input']
    namelist_wps   = config['namelist_wps']
    
    wrfout_dir    = '%s/wrfout'   %(model_run_dir)
    log_dir       = '%s/log'      % model_run_dir    
    rsl_dir       = '%s/rsl'      % model_run_dir
    namelist_dir  = '%s/namelist' % model_run_dir
    run_key       = '%s.%s'       %(domain, model_run)    # composite key  

    logger.debug('Moving wrfout files from %s to %s' %(wrf_run_dir, wrfout_dir) )

    # Move WRF output files to new directory
    flist = glob.glob(wrf_run_dir+'/wrfout*')
    transfer(flist, wrfout_dir, mode='move', debug_level='debug')

    # Move log files to new directoy
    #flist = glob.glob(wrf_run_dir+'/rsl.*')
    #transfer(flist, rsl_dir, mode='move', debug_level='debug')

    cmd = 'cp %s %s/namelist.input.%s.%s' % (namelist_input, namelist_dir, run_key, init_str)
    run_cmd(cmd, config)
    
    cmd = 'cp %s/namelist.wps %s/namelist.wps.%s.%s' % (model_run_dir, namelist_dir, run_key, init_str)
    run_cmd(cmd, config)


    #
    # Archive log files
    # 
    logger.debug('moving rsl files to %s' % rsl_dir )
    cmd = 'cp %s/rsl.out.0000 %s/rsl.out.%s' %(wrf_run_dir, rsl_dir, run_key)
    run_cmd(cmd, config)
    


def archive(config):
    """Tidies up directory structure, ensures namelist and log files are archived. 
    Archive only needs to be run once per model run, not for each nest. Assumes that both the
    namelist.input and namelist.wps appear in the model_run directory"""

    logger = get_logger()    
    logger.info('*** MOVING FILES TO BACKUP ***')


    domain        = config['domain']
    domain_dir    = config['domain_dir']
    wrf_model_run_dir   = config['wrf_dir']+'/run'
    model_run     = config['model_run']
    backup_base   = config['backup_dir']
    archive_mode   = config['archive_mode']
    backup_dirs   = config['backup_dirs']       # These are the directories to archive/backup
    
    model_model_run_dir    = '%s/%s'      %(domain_dir, model_run)
    model_run_backup = '%s/%s/%s'   %(backup_base, domain, model_run)
  
    
    wrfout_dir    = '%s/wrfout'        % model_model_run_dir
    wrfpost_dir   = '%s/wrfpost'       % model_model_run_dir
    log_dir       = '%s/log'           % model_model_run_dir
    rsl_dir       = '%s/rsl'           % model_model_run_dir
    namelist_dir  = '%s/namelist'      % model_model_run_dir

    for bd in backup_dirs:
        logger.debug('archiving files in %s' % bd)
        #
        # Remember the trailing slash!
        #
        source = '%s/%s/' % (model_model_run_dir, bd)
        target = '%s/%s' % (model_run_backup, bd)
        rsync(source, target, config)
    
    #rsync(wrfpost_dir, model_run_backup,config)
    #rsync(log_dir, model_run_backup,config)
    #rsync(rsl_dir, model_run_backup,config)
    #rsync(namelist_dir, model_run_backup,config)



def grb_to_backup(config):
    """Transfers all files in the archive domain to the backup directory """
    domain        = config['domain']
    domain_dir    = config['domain_dir']
    wrf_model_run_dir   = config['wrf_dir']+'/run'
    model_run     = config['model_run']
    backup_dir    = config['backup_dir']
    wrfout_dir    = '%s/%s/wrfout' %(domain_dir, model_run)
    model_model_run_dir = '%s/%s'   %(domain_dir, model_run)
    log_dir       = '%s/logs' % domain_dir    
    archive_dir   = '%s/%s/archive' %(domain_dir,model_run)
    run_key       = '%s.%s'   %(domain, model_run)    # composite key      
    backup_dir    = '%s/%s/%s' % (backup_dir, domain, model_run)
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    cmd = 'mv %s/wrfpost* %s' % (archive_dir, backup_dir)
    run_cmd(cmd, config)


def grb_from_backup(config):
    """Transfers one file in the backup domain to the archive directory based on 
    init_time """
    
    domain        = config['domain']
    domain_dir    = config['domain_dir']
    init_time     = config['init_time']
    dom           = config['dom']
    model_run     = config['model_run']
    backup_base_dir    = config['backup_dir']
    model_model_run_dir = '%s/%s'   %(domain_dir, model_run)
    archive_dir   = '%s/%s/archive' %(domain_dir,model_run)
    run_key       = '%s.%s'   %(domain, model_run)    # composite key      
    backup_dir    = '%s/%s/%s' % (backup_base_dir, domain, model_run)
    
        
    wrfpostname = 'wrfpost_d%02d_%s.grb'%(dom,init_time.strftime('%Y-%m-%d_%H'))
    if not os.path.exists(wrfpostname):
        raise IOError('Could not find grb file in backup: %s' % wrfpostname)
    
    cmd = 'cp %s/%s %s' % (backup_dir, wrfpostname, archive_dir)
    run_cmd(cmd, config)




    
def run_unipost(config):
    """ Runs the Universal Post Processor for each forecast time. 
    Translated from the run_unipost_frames shell script. A post-processing
    directory should exist, specified by the post_dir entry in config, and
    the UPP control file wrf_cntrl should exist within this directory.
    
    TODO: tidy up some of the hangovers from the shell script version
    
    Arguments:
    config -- dictionary containing various configuration options
    
    """
    logger = get_logger()    
    logger.info('*** RUNNING UNIVERSAL POST PROCESSOR ***')
    
    domain_dir    = config['domain_dir']
    max_dom       = config['max_dom']
    dom           = config['dom'] # current domain number
    model_run     = config['model_run']
    wrfout_dir    = '%s/%s/wrfout' %(domain_dir, model_run)    


    post_dir      = '%s/%s/postprd' % (domain_dir, model_run)
    wrf_cntrl     = post_dir+'/wrf_cntrl.parm'
    upp_dir       = config['upp_dir']
    wrf_model_run_dir   = config['wrf_dir']+'/run'
    namelist      = read_namelist(wrf_model_run_dir+'/namelist.input')

    fcst_times    = get_fcst_times(config)    
    init_time     = fcst_times[0]
    history_interval = config['history_interval']
    grb_fmt       = config['grb_fmt']


    #----CREATE DIRECTORIES-----------------------------------------------
    # Create archive directories to store data and settings
    #---------------------------------------------------------------------


    wrfpost_dir    = '%s/%s/wrfpost' %(domain_dir,model_run)

    if not os.path.exists(wrfpost_dir):
        os.makedirs(wrfpost_dir)

    #----PREPARATION-------------------------------------------------------
    # Link all the relevant files need to compute various diagnostics
    #---------------------------------------------------------------------
    
    #
    # Everything is done within the postprd directory
    #
    logger.debug('Going into postprd directory: %s' %post_dir)
    #os.chdir(post_dir)

    #
    # Clean up old output files
    #
    #logger.debug('Removing old output files')
    cmd = 'rm -f %s/*.out' % post_dir
    run_cmd(cmd, config)
    cmd = 'rm -f %s/*.tm00' % post_dir
    run_cmd(cmd, config)
    
    
    # Link Ferrier's microphysic's table and Unipost control file, 
    cmd = 'ln -sf %s/ETAMPNEW_DATA ./eta_micro_lookup.dat' % wrf_model_run_dir
    run_cmd(cmd, config)
    
    #
    # Get local copy of parm file
    # no - lets force the user to manually ensure a copy is placed
    # in the postprd diretory first
    # os.system('ln -sf ../parm/wrf_cntrl.parm .')
    
    #
    # Check wrf_cntrl file exists
    #
    if not os.path.exists(wrf_cntrl):
        raise IOError('could not find control file: %s'% wrf_cntrl)
    
    
    #
    # link coefficients for crtm2 (simulated GOES)
    # Jeez - these should really get called via run_cmd for 
    # consistency, but I can't be chewed right now
    #
    CRTMDIR  = upp_dir+'/src/lib/crtm2/coefficients'
    os.system('ln -fs %s/EmisCoeff/Big_Endian/EmisCoeff.bin           ./' %CRTMDIR)
    os.system('ln -fs %s/AerosolCoeff/Big_Endian/AerosolCoeff.bin     ./' %CRTMDIR)
    os.system('ln -fs %s/CloudCoeff/Big_Endian/CloudCoeff.bin         ./' %CRTMDIR)
    os.system('ln -fs %s/SpcCoeff/Big_Endian/imgr_g12.SpcCoeff.bin    ./' %CRTMDIR)
    os.system('ln -fs %s/TauCoeff/Big_Endian/imgr_g12.TauCoeff.bin    ./' %CRTMDIR)
    os.system('ln -fs %s/SpcCoeff/Big_Endian/imgr_g11.SpcCoeff.bin    ./' %CRTMDIR)
    os.system('ln -fs %s/TauCoeff/Big_Endian/imgr_g11.TauCoeff.bin    ./' %CRTMDIR)
    os.system('ln -fs %s/SpcCoeff/Big_Endian/amsre_aqua.SpcCoeff.bin  ./' %CRTMDIR)
    os.system('ln -fs %s/TauCoeff/Big_Endian/amsre_aqua.TauCoeff.bin  ./' %CRTMDIR)
    os.system('ln -fs %s/SpcCoeff/Big_Endian/tmi_trmm.SpcCoeff.bin    ./' %CRTMDIR)
    os.system('ln -fs %s/TauCoeff/Big_Endian/tmi_trmm.TauCoeff.bin    ./' %CRTMDIR)
    os.system('ln -fs %s/SpcCoeff/Big_Endian/ssmi_f15.SpcCoeff.bin    ./' %CRTMDIR)
    os.system('ln -fs %s/TauCoeff/Big_Endian/ssmi_f15.TauCoeff.bin    ./' %CRTMDIR)
    os.system('ln -fs %s/SpcCoeff/Big_Endian/ssmis_f20.SpcCoeff.bin   ./' %CRTMDIR)
    os.system('ln -fs %s/TauCoeff/Big_Endian/ssmis_f20.TauCoeff.bin   ./' %CRTMDIR)
    
    os.putenv('MP_SHARED_MEMORY', 'yes')
    os.putenv('MP_LABELIO', 'yes')
    os.putenv('tmmark', 'tm00')
    
    
    #
    # Run unipost for each time in the output file
    # Note that unipost names the intermediate files
    # WRFPRShhh.tm00 where hhh is the forecast hour
    #
    for n,t in enumerate(fcst_times):
    
        current_time = t.strftime('%Y-%m-%d_%H:%M:%S')
        fhr          = n*history_interval/60
        #logger.debug('post processing time %s, fhr %d ' % (current_time, fhr))

        #
        # Assume the forecast is contained in one wrfout file 
        # named according to the forecast initial time
        #
        wrfout = '%s/wrfout_d%02d_%s' %(wrfout_dir,dom, init_time.strftime('%Y-%m-%d_%H:%M:%S'))
        #logger.debug('looking for file: %s' % wrfout)
        
        #--- itag file --------------------------------------------------------
        #   Create input file for Unipost
        #   First line is where your wrfout data is
        #   Second line is the format
        #   Third line is the time for this process file
        #   Forth line is a tag identifing the model (WRF, GFS etc)
        #----------------------------------------------------------------------
        #logger.debug('writing itag file')
        #logger.debug('time in itag file: %s' %current_time)
        itag = open('itag', 'w')
        itag.write('%s\n'%wrfout)
        itag.write('netcdf\n')
        itag.write('%s\n'%current_time)
        itag.write('NCAR\n')
        itag.close()
        
        #-----------------------------------------------------------------------
        #  Check wrf_cntrl.parm file exists
        #-----------------------------------------------------------------------            
        
        
        
        #-----------------------------------------------------------------------
        #   Run unipost.
        #-----------------------------------------------------------------------            
        os.system('rm -f fort.*')
        os.system('ln -sf wrf_cntrl.parm fort.14')
        os.system('ln -sf griddef.out fort.110')
        cmd = '%s/bin/unipost.exe < itag > unipost_d%02d.%s.out 2>&1' %(upp_dir, dom,current_time)
        run_cmd(cmd, config)
        
        tmp_name = 'WRFPRS%03d.tm00' % fhr
        grb_name = 'wrfpost_d%02d_%s.tm00' %(dom,current_time)
        
        #
        # If keeping same format, just move output file
        #
        cmd = 'mv %s %s' %(tmp_name, grb_name)
        run_cmd(cmd, config)
        
        #
        # Convert to grib2 format if required
        #            
        #if grb_fmt=='grib2':
        #    cmd = 'cnvgrib -g12 %s %s' %(tmp_name, grb_name) 
        #    run_cmd(cmd, config)
            
    logger.debug('concatenating grib records into single file for domain dom %02d...' %dom)
    outname = 'wrfpost_d%02d_%s.grb'%(dom,init_time.strftime('%Y-%m-%d_%H'))
    cmd     = 'cat wrfpost_d%02d_*.tm00 > %s' %(dom, outname)
    run_cmd(cmd, config)

    
    #-----------------------------------------------------------------------
    # Archive
    #-----------------------------------------------------------------------
    cmd = 'mv %s %s' %(outname, wrfpost_dir)

    ret = run_cmd(cmd, config)
    
    if ret!=0:
        raise IOError('could not move post-processed output')
  
  
    logger.info("*** SUCESS UPP ***")


def convert_grib(config):
    """Converts the grib1 outputs of UPP to grib2 format, mainly so the wgrib2 tool 
    can be used to extract csv time series from it.
    
    
    Should not rely on globbing directories here. Could have nasty consequences,
    e.g. conversion of too many files etc """

    logger=get_logger()
    logger.debug('*** CONVERTING GRIB1 TO GRIB2 ***')
    domain_dir = config['domain_dir']
    model_run  = config['model_run']
    init_time  = config['init_time']
    dom        = config['dom']
    
    
    
    f1 = '%s/%s/archive/wrfpost_d%02d_%s.grb' % (domain_dir, model_run, dom, init_time.strftime('%Y-%m-%d_%H'))
    f2 =  f1.replace('.grb', '.grib2')
    cmd = 'cnvgrib -g12 %s %s' %(f1, f2)
    run_cmd(cmd, config)
    


def read_fcst_series(fname):
    """ Reads formatted time series"""

    logger = get_logger()
    logger.debug('reading tseries file %s' % fname)
    
    #
    # Current format of time series files is:
    # domain_dir  , model_run, dom, fhr, valid,              init,                var, obs_sid,  lat,   lon,  hgt, val
    # baseline_gfs, test,      A,          01, 00, 2006-11-30 12:00:00, 2006-11-30 12:00:00, UGRD, ormonde,  58.1,  -3.0, 100, 3.416
    #


    names =  ['domain', 'model_run', 'grid_id', 'fhr', 'valid_time', 'init_time', 'var', 'obs_sid', 'lat', 'lon', 'hgt', 'val']
    converters = {4: strptime, 5: strptime}
    
    rec = np.genfromtxt(fname, delimiter=',', names=names, dtype=None, converters=converters)
    return rec


def read_obs_series(fname):
    """ Reads formatted time series"""

    logger = get_logger()
    logger.debug('reading tseries file %s' % fname)
    
    #
    # Current format of time series files is:
    # valid, var, obs_sid,  lat,   lon,  hgt, val
    # baseline_gfs, test,      A,          01, 00, 2006-11-30 12:00:00, 2006-11-30 12:00:00, UGRD, ormonde,  58.1,  -3.0, 100, 3.416
    #


    #names =  ['domain', 'model_run', 'test_case', 'grid_id', 'fhr', 'valid_time', 'init_time', 'var', 'obs_sid', 'lat', 'lon', 'hgt', 'val']
    names = ['valid_time', 'var', 'obs_sid', 'lat', 'lon', 'hgt', 'val']
    converters = {0: strptime}
    
    rec = np.genfromtxt(fname, delimiter=',', names=names, dtype=None, converters=converters)
    return rec


def read_wgrib_time_series(fname):
    """Reads 'time series' file written by wgrib2 """
    
    logger = get_logger()
    logger.debug('reading tseries file %s' % fname)
    hour   = datetime.timedelta(0, 60*60) 
    
    f = open(fname, 'r')
    times = []
    vals  = []
    for line in f:
        tokens    = line.split(':')
        init_str  = tokens[2]
        init_time = datetime.datetime(*time.strptime(init_str, 'd=%Y%m%d%H')[0:5])
        fhr_token = tokens[5].split()[0].replace('anl', '0')
        fhr       = int(fhr_token)
        valid_time = init_time + fhr * hour
        val         = float(tokens[7].split('=')[-1].strip('\n'))
        times.append(valid_time)
        vals.append( val)
  
    f.close()
    return (times, vals)



def timing(config):
    """Reads a rsl file from WRF and works out timing information
    from that """

    #
    # Where should we assume to find the rsl file?
    # In the wrf_model_run_dir
    #
    logger = get_logger()
    logger.info('*** Computing timing information ***')
    wrf_run_dir    = config['wrf_run_dir']
    rsl_file       = '%s/rsl.error.0000' % wrf_run_dir
    namelist_input = config['namelist_input']
    namelist       = read_namelist(namelist_input).settings
    timestep       = namelist['time_step'][0]
    f              = open(rsl_file, 'r')
    lines          = f.read().split('\n')
    
    # get timings on outer domain
    main_times  = [float(l.split()[8]) for l in lines if re.search("^Timing for main: time .* 1:", l)]
    total       = sum(main_times)
    steps       = len(main_times)
    time_per_step = (total/steps)
    x_real       = timestep / time_per_step
    logger.info('*** TIMING INFORMATION ***')
    logger.info('\t %d outer timesteps' % steps)
    logger.info('\t %0.3f elapsed seconds' % total)
    logger.info('\t %0.3f seconds per timestep' % time_per_step )
    logger.info('\t %0.3f times real time' %x_real)
    logger.info('*** END TIMING INFORMATION ***')

def run_scripts(config):
    """Simply runs whatever scripts are specified in the config file. 
    Sets a few environment variables first """
    logger = get_logger()
    
    
    domain_dir     = config['domain_dir']
    domain         = config['domain']
    model_run      = config['model_run']
    init_time      = config['init_time']
    nest_id        = config['dom']
    loc_file       = config['locations_file']
    scripts        = config['run_scripts']
    
    fcst_file      = '%s/%s/wrfout/wrfout_d%02d_%s:00:00.nc' %(domain_dir, model_run, nest_id, init_time.strftime("%Y-%m-%d_%H"))

    os.environ['FCST_FILE']      = fcst_file
    os.environ['LOCATIONS_FILE'] = loc_file
    os.environ['NEST_ID']        = str(nest_id)
    logger.info('*** RUNNING ADDITIONAL SCRIPTS ***')
    logger.warn('Checking success of external scripts is not yet implemented')
    for s in scripts:
        run_cmd(s, config)
    
    logger.info('*** FINISHED ADDITIONAL SCRIPTS ***')

def run_point_stat(config):
    """ Runs the point_stat tool. 
    
    Note that point_stat produces a fixed set of fields. If we want to compare
    outputs from multiple similar runs, we have to make use of one of the fields
    to do this. The 'MODEL' field is probably the most suitable field to use for
    this purpose, but it needs to be set in PointStatConfig, and may interfere with 
    later assumptions when processing mpr_files. The 'VERSION' field is another option.
    
    Arguments:
    config -- dictionary containing various configuration options
    
    """
    
    logger         = get_logger()    
    max_dom        = config['max_dom']
    met_dir        = config['met_dir']
    domain_dir     = config['domain_dir']
    domain         = config['domain']
    dom            = config['dom']        # integer number rather than name
    model          = config['model']
    model_run      = config['model_run']
    bdy_conditions = config['bdy_conditions']
    tmp_dir        = config['tmp_dir']
    ps_config      = config['ps_config'] 
    
    logger.info('*** RUNNING MET POINT STAT ***')
    
    #
    # Generate a tag to write to the 'MODEL' field in mpr files
    #
    wk_dir      = domain_dir
    grb_dir     = '%s/%s/archive' %(domain_dir,model_run)

    fcst_times  = get_fcst_times(config) 
    init_time   = fcst_times[0]
    run_hours   = config['fcst_hours']
   
    grb_file    = '%s/wrfpost_d%02d_%s.grb' %(grb_dir, dom, init_time.strftime('%Y-%m-%d_%H'))
    obs_file    = config['obs_file']

    if not os.path.exists(grb_file):
        raise IOError('could not find file: %s' %grb_file)



    #
    # Stored stat files domain, model run and initial time
    #        
    #out_dir     = '%s/%s/stats/%s/d%02d' %(domain_dir, model_run, init_time.strftime('%Y-%m-%d_%H'), dom)
    out_dir     = '%s/%s/stats' %(domain_dir, model_run)
    out_file    = '%s/%s.%s.%s.d%02d.%s.mpr' %(out_dir, domain, model, model_run, dom, init_time.strftime('%Y-%m-%d_%H'))

    #
    # Write stat files to temporary directory first, then post-process to final directory
    #
    clear_tmp_dir(tmp_dir, config)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    
    #***************************************************
    # Run point_stat
    #**************************************************
    
    #
    # Modify PointStatConfig to ensure model field is correct
    #
    os.chdir(wk_dir)
    cmd = """sed -i'.backup' -e's/^model.*/model  = "%s";/g' %s""" %(model, ps_config)
    run_cmd(cmd, config)
    
    logger.debug('grb: %s' %grb_file)
    logger.debug('obs: %s' %obs_file)
    
    #
    # Remove any existing point-stat files for this initial time
    #
    #logger.debug('removing old point-stat files\n')
    #cmd = 'rm -f %s/point_stat_*_%sV_cnt.txt' %(out_dir, init_time.strftime(ps_format))
    #logger.debug(cmd+'\n')
    #os.system(cmd)
    
    for n,fcst_time in enumerate(fcst_times):
        #
        # Work out decimal number of hours
        #
        logger.debug('processing forecast valid: %s' %fcst_time.strftime(ps_format))
        
        delta   = fcst_time - init_time
        days    = delta.days
        seconds = delta.seconds
        fhr   = 24*days + (seconds / (60.0 * 60.0))
    
        #
        # In the output files, any fractional part is represented by four
        # decimal digits after the first two
        #
        frac_digits = int((fhr - int(fhr))*1000)
        
        logger.debug('calculated lead time: %0.3f hours' % fhr)
        logger.debug('*** EXECUTING POINT STAT ***')

        #
        # Use tmp dir as output directory for now
        #
        #point_stat(met_dir, grb_file, obs_file, tmp_dir, ps_config, fcst_time, fhr)

        cmd = '%s/bin/point_stat %s %s %s -fcst_valid %s -fcst_lead %03d -outdir %s -v 3' %(met_dir, 
                                                                                          grb_file, 
                                                                                          obs_file,
                                                                                          ps_config,
                                                                                          fcst_time.strftime(ps_format),
                                                                                          fhr,
                                                                                          tmp_dir)    
        run_cmd(cmd, config)

        
        #
        # Run sed command to add meta-data
        #
        #run_cmd(cmd, config)       

        
    #
    # Post-process stat files from tmp directory into 
    # output directory.
    # The output files will be standard mpr and .stat files. We can doctor these to add in some 
    # more columns including metadata.
    #
    mpr_files = sorted(glob.glob('%s/*_mpr.txt' % tmp_dir))
    if os.path.exists(out_file):
        os.remove(out_file)
    
    #
    # Write a header? Headers are informative, but can be a pain for concatenating 
    # or importing into databases
    #
    #in_file   = mpr_files[0]
    #cmd = """head -1 %s | awk '{print "DOMAIN MODEL_RUN NEST " $0}' > %s """ % (in_file, out_file)
    #logger.debug(cmd)
    #subprocess.call(cmd, shell=True)
    
    #
    # Process all mpr files. If we want awk to replace mutliple spaces with just one space
    # which is a useful side effect for importing into a database, we must give each field explicitly
    # There are 32 fields in the original mpr files written by MET.
    #
    # This is a bit ugly, and should really get tidied up! 
    # In case anyone else has to make sense of this, here is what is happening.
    # Awk is used to insert extra metadata columns.
    # Awk is then used to print all the remaining fields, seperated by a single space.
    # Sed is used to strip the header line.
    #
    nfields = 31
    for f in mpr_files:
        awk_fields = ' '.join(['" "$%01d' % n for n in range(1, nfields+1)])
        cmd = """awk '{print "%s %s %02d" %s}' %s | sed 1d >> %s """ %(domain, model_run, dom, awk_fields, f, out_file)       
        run_cmd(cmd, config)        
   



    logger.info('*** SUCESS MET POINT STAT ***')





def run_point_stat_gfs(config):
    """ Runs the point_stat tool against GFS output.
    
    This works on the same loop as the other functions, designed to be called 
    once per initial time.
    
    This raises a question as to how we want to archive our GFS files.
    We could store each forecast hour in a seperate file, or we could 
    concatenate all forecast hours into one file per forecast, which may 
    be easier.  
    
    Arguments:
    config -- dictionary containing various configuration options"""
    
    logger      = get_logger()    
    logger.debug('hard coded GFS domain in function: remove')
    
    domain_dir  = '/home/slha/domains/GFS'
    met_dir     = config['met_dir']
    wk_dir      = domain_dir+'/met'
    grb_dir     = config['extract_dir']
    grb_fmt     = config['grb_input_fmt']
    fcst_times  = get_fcst_times(config) 
    init_time   = fcst_times[0]
    run_hours   = config['fcst_hours']
    obs_file    = config['obs_file']
    filelist    = get_bdy_filenames(config)
    ps_config   = domain_dir + '/PointStatConfig'
    for f in filelist:
        logger.debug(f)
    
    #
    # There is no easy way of getting back the initial time from 
    # the point stat files, so we keep them in seperate directions
    #
    out_dir     = '%s/stats/%s' %(domain_dir, init_time.strftime('%Y-%m-%d_%H'))
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    #
    # Remove any existing point-stat files for this valid time
    #
    logger.debug('removing old point-stat files')
    cmd = 'rm -f %s/point_stat_*_%sV_cnt.txt' %(out_dir, init_time.strftime(ps_format))
    #logger.debug(cmd)
    #os.system(cmd)
    
    
    for n,fcst_time in enumerate(fcst_times):
        #
        # Work out decimal number of hours
        #
        logger.debug('processing forecast valid: %s' %fcst_time.strftime(ps_format))
        
        delta   = fcst_time - init_time
        days    = delta.days
        seconds = delta.seconds
        fhr     = 24 * days + (seconds / (60.0 * 60.0))
        
        grb_file = bdy_filename(grb_dir, grb_fmt, init_time, fhr)
        
        
        #
        # Run point_stat
        #
        os.chdir(wk_dir)
        logger.info('*** EXECUTING POINT STAT ***')
        logger.info('grb: %s' %grb_file)
        logger.info('obs: %s' %obs_file)
    
        #
        # In the output files, any fractional part is represented by four
        # decimal digits after the first two
        #
        frac_digits = int((fhr - int(fhr))*1000)
        
        logger.debug('calculated lead time: %0.3f hours' % fhr)
        point_stat(met_dir, grb_file, obs_file, out_dir, ps_config, fcst_time, fhr)
        
        
        cmd = '%s/bin/point_stat %s %s PointStatConfig -fcst_valid %s -fcst_lead %03d -outdir %s -v 3' %(met_dir, 
                                                                                          grb_file, 
                                                                                          obs_file,
                                                                                          fcst_time.strftime(ps_format),
                                                                                          fhr,
                                                                                          out_dir)
        logger.debug(cmd)
        subprocess.call(cmd, shell=True)
    
    return 0    
    
    




def extract_gfs_fields(config):
    """ Creates grib1 extract from GFS based on grib_extract specified in config.
    Calls wgrib2 using egrep to extact fields, then calls 
    grbconv to convert those to grib1 format.
    
    Arguments:
    config -- dictionary containing various configuration options
    
    """
    logger = get_logger()    
    logger.debug('extracting 10m wind to grib1 format')
    #
    # Question is where we store the 
    #
    gribmaster_dir  = config['gribmaster_dir']
    tmp_dir         = config['tmp_dir']
    extract_dir     = config['extract_dir']
    grib_extract    = config['grib_extract']
    tmp_dir         = config['tmp_dir']
    
    clear_tmp_dir(tmp_dir)
    logger.debug('gribmaster_dir: %s' % gribmaster_dir)
    logger.debug('tmp_dir: %s'        % tmp_dir)
    logger.debug('extract_dir: %s'    % extract_dir)
    logger.debug('grib_extract:%s'    % grib_extract)
    
    #
    # Get all boundary conditions associated with this forecast
    #
    bdy_filenames   = get_bdy_filenames(config)
    for f in bdy_filenames:
        name_ext = os.path.split(f)[1]
        parts    = name_ext.split('.')
        name     = parts[0]
        ext      = parts[1]
        
        
        ename = name.replace('Europe', 'Extract')
        epath = '%s/%s' %(extract_dir, ename)
        extract_name = '%s.%s' %(epath, ext)
        
        #
        # Extract the fields based on grid_extract expression
        #
        cmd = 'wgrib2 %s | egrep %s | wgrib2 -i %s -grib %s ' %(f, grib_extract, f, extract_name)
        
        
        logger.debug(cmd)
        subprocess.call(cmd, shell=True)
        grib1_name = '%s.grib1' % epath
        cmd = '%s/bin/cnvgrib -g21 %s %s' %( gribmaster_dir,extract_name,grib1_name) 
        logger.debug(cmd)
        subprocess.call(cmd, shell=True)
    
   
    


def cleanup(config):
    """Cleans up various files """
    logger = get_logger()

    init_time = config['init_time']
    post_clean = config['post_clean']
    cleanup_dir = [sub_date(s, init_time=init_time) for s in post_clean]
    
    for d in cleanup_dir:
        cmd = 'rm -f %s' % d
        logger.debug(cmd)
        #run_cmd(cmd, config)

    logger.info('*** FINISHED CLEANUP ***')
