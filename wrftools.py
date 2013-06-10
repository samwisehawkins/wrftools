#*************************************************************************************
# Module wrftools
#
# Provides a selection of functions for pre-processing and
# running a WRF forecast.  
# 
# Author: Sam Hawkins sam.hawkins@vattenfall.com
#
# Assumed domains directory structure:
# domain_dir     --> all config files, namelist.wps etc.
#       /geo_em  --> outout from geogrid     
#       /met_em  --> output from metgrid
#       /model_run --> namelist.input file and other settings specific to that run
#           /wrfout  --> netcdf output from WRF
#           /wrfpost     --> grib output from UPP
#           /tseries
#           /postprd               --> directory for doing post-processing        
#           /stats/init_time/dom   --> mpr output from point_stat 
#           /plots/init_time       --> graphical output from NCL
#
#
# A locations file controls which variables get written to out to time series
# This should have the format:
# # comments
# name,   lat,  lon, height, vars
# THANET,  58.0, 1.5, 80:90,  U:V:SPEED
#
# where height and vars can be lists with elements separated by :
#
# Time series output files will be named according to:
# domain/model_run/tseries/U_80_2006-11-30_00.csv 
#
# IDEAS
# How do we create a new model-run?  The current option is to 
# create a new sub-directory within the domain dir.  An optionaly way 
# would just be to edit the the config file and let the creation be
# done automagically? Actually, the way we do now isn't so difficult.
#
# TODO
# * change run_unipost to allow sub-hourly output
# * Change namelist reading code to strip trailing commas and remove trailing quotes -- done
# * Summarise file transfers in logging output
#
# CHANGES
#
#
# 2013-02-04 Rationalised the movement to and from /longbackup, now uses rsync for
#             flexibility
#
# 2012-12-10 Implemented a more aggressive cleanup to remove WPS leftover files
#
#
# 2012-09-13 Updated structure to support operational forecasting, using flag 
#            operational=.true. get_cases still needs tidying up
#
# 2012-09-05 Uses PyNIO as interpolation, as cnvgrib was failing, meaning time-series
#            could not be extracted.
#
# 2012-07-27 Added functionality for writing out time series, reading time series
#            reading power curves, and converting wind speeds into powers
#
# 2012-07-19 Changed shell calls to use run_cmd in order to have enable dummy runs
#            where commands are not executed.
#
# 2012-05-*  Updated point stat to make much more use of metadata in the output
#            in order to facillitate better breakdown of stats when read into database
#
# 2012-03-30 Updated run_point_stat to write a more descriptive tag into the 
#            'MODEL' field for use in statistical analysis
#
# 2012-03-05 Updated functions to operate on one domain only, reading value
#            from config[dom], and putting looping structure outside.
#
#
#
#*************************************************************************************

import os
import subprocess
import sys
import re
import traceback
import math
import numpy as np
import glob
import time, datetime
from dateutil import rrule
from namelist import Namelist, read_namelist

from visualisation import *
import logging

from tseries import extract_tseries, power, tseries_to_json, json_to_web


LOGGER         = 'wrf_forecast'

in_format       = "%Y-%m-%d %H:%M:%S" 
out_format      = "%Y-%m-%d_%H:%M:%S"
ps_format       = "%Y%m%d_%H%M%S"          # date format for point stat



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
    
    logger = get_logger()
    cmd = 'mpirun -n %d -hostfile %s %s' % (num_procs, hostfile, cmd)
    logger.debug(cmd)
    
    t0          = time.time()
    if run_level=='RUN':
        ret = subprocess.call(cmd, shell=True)        
    else:
        ret = 0
    
    telapsed = time.time() - t0
    if cmd_timing:
        logger.debug("done in %0.1f seconds" %telapsed)
    
    return ret

def run_cmd(cmd, config):
    """Executes and logs a shell command. If config['run_level']=='DUMMY', then
    the command is logged but not executed.
    
    Dealing with output from external scripts is pretty tricky. Do we want to log them 
    via the python logger? That would be nice, but prevents us from examining 
    the output from files such as ungrib.log. Allow redirection to python 
    logger using redirect=True
    
    """
    
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
    """Ensures that certain files and subdirectories are present."""
    
    config['domain']
    config['model']
    config['model_run']
    run_dir = config['run_dir']

    logger           = get_logger()
    logger.info('*** PREPARING DIRECTORIES ***')
    logger.debug("check_directories called")
    if not os.path.exists(run_dir):
        os.makedirs(run_dir)
    subdirs = ['wrfout','plots', 'tseries', 'json', 'rsl', 'namelist', 'met_em', 'postprd'] 
    fulldirs = [ run_dir+'/'+d for d in subdirs ]
    for d in fulldirs:
        if not os.path.exists(d):
            logger.debug('creating directory %s ' %d)
            os.mkdir(d) 
   
    for log in ['ncl_log', 'gm_log']:
        log_file = config[log]
        if os.path.exists(log_file):
            logger.debug('removing log file: %s' % log_file )
            os.remove(log_file) 

    logger.info('*** DONE PREPARE ***')






#*****************************************************************
# Post-checking logging
#*****************************************************************
def summarise(config):
    """Reports which file exist in different directories """
    logger           = get_logger()
    config['domain']
    config['model']
    config['model_run']
    init_time = config['init_time'] 
    run_dir   = config['run_dir']
    web_dir   = sub_date(config['web_dir'], init_time)
    
    flist = glob.glob(web_dir+'/*')
    for filename in sorted(flist):
        info  = os.stat(filename)
        mtime = datetime.datetime.fromtimestamp(info.st_mtime)
        logger.info('%s : %s ' %(filename, mtime.strftime('%Y-%m-%d %H:%M')))



#*****************************************************************
# Date/time functions
#*****************************************************************



#*****************************************************************
# Forecast functions
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
    end_time = init_time + fcst_hours*hour
    
    
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

def get_bdy_filenames(config):
    """ Creates a list of boundary conditions filenames
    based on the information in config
    
    TODO: remove hard coding of filenames. Should be specified 
    entirely from config file.
    
    Arguments:
    config -- dictionary containing various configuration options
    
    """

    logger       = get_logger()
    logger.debug('*** GENERATING BOUNDARY CONDITION FILENAMES ***')

    grb_dir       = config['grb_dir']
    grb_fmt       = config['grb_input_fmt']
    bdy_interval  = config['bdy_interval']
    
    init_time     = config['init_time']
    fcst_hours    = config['fcst_hours']
    bdy_times     = get_bdy_times(config)
    

    filelist = ['%s/%s' %(grb_dir, bdy_filename(init_time, b, grb_fmt)) for b in bdy_times]
    return filelist    
 
    

def bdy_filename(init_time, bdy_time, fmt):

    master_fmt = fmt[0]
    date_fmt   = fmt[1]
    init_str = init_time.strftime(date_fmt)
    valid_str = bdy_time.strftime(date_fmt)
    opt      = {'init_time' : init_str,
                'valid_time' : valid_str}
    

    delta   = bdy_time - init_time
    fhr     = delta.days*24 + delta.seconds/3600

    if len(fmt)>2:
        fhr_fmt   = fmt[2]
        fhr_str   = fhr_fmt % fhr
        opt['fhr']=  fhr_str

    filename = master_fmt % opt
    return filename                     


def run_gribmaster(config):
    """Runs the gribmaster programme to download the most recent boundary conditions """
    logger      = get_logger()
    gm_dir      = config['gm_dir']
    gm_transfer = config['gm_transfer']
    gm_dataset  = config['gm_dataset']
    start       = config['init_time']
    fcst_hours  = config['fcst_hours']
    gm_log      = config['gm_log']
    gm_sleep    = config['gm_sleep']
    gm_max_attempts = int(config['gm_max_attempts'])


    log_dir = '/home/slha/forecasting'
       
    cmd     = '%s/gribmaster --verbose --%s --dset %s --date %s --cycle %s --length %s > %s' %(gm_dir, gm_transfer, gm_dataset, start.strftime('%Y%m%d'), start.strftime('%H'), fcst_hours, gm_log )
    logger.debug(gm_max_attempts)
    logger.debug(type(gm_max_attempts))
    for attempt in range(gm_max_attempts):
        logger.info('*** RUNNING GRIBMASTER, %s attempt ***' % (attempt+1))
        run_cmd(cmd, config)
        
        cmd = 'grep "BUMMER" %s' % gm_log # check for failure
        ret = subprocess.call(cmd, shell=True)
        # if we positively find the string BUMMER, we know we have failed
        if ret==0:
            logger.error('*** FAIL GRIBMASTER: Attempt %d of %d ***' % (attempt+1, gm_max_attempts))
            logger.info('Sleeping for %d mins' % gm_sleep) 
            time.sleep(gm_sleep*60)
        
        # else we check for definite sucess
        else:
            cmd = 'grep "ENJOY" %s' % gm_log # check for failure
            ret = subprocess.call(cmd, shell=True)
            if ret==0:
                logger.info('*** SUCESS GRIBMASTER ***')
                return
        
        
    raise IOError('gribmaster did not find files after %d attempts' % gm_max_attempts)

    

def sub_date(s, dt):
    """Substitues a date into a string following standard format codes"""
    
    y  = str(dt.year)
    m  = '%02d' % dt.month
    d  = '%02d' % dt.day
    H  = '%02d' % dt.hour
    M  = '%02d' % dt.minute
    S  = '%02d' % dt.second

    s1 = s.replace('%Y', y)
    s2 = s1.replace('%y',y)
    s3 = s2.replace('%m',m)
    s4 = s3.replace('%d', d) 
    s5 = s4.replace('%H', H)
    s6 = s5.replace('%M', M)
    s7 = s6.replace('%S', S)
    return s7

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
    sst_filename   = sub_date(base_filename, sst_time)
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
    tmp_dir      = config['tmp_dir']
    domain_dir   = config['domain_dir']
    model_run    = config['model_run']
    init_time    = config['init_time']
    max_dom      = config['max_dom']
    sst_local_dir = config['sst_local_dir']
    sst_time     = get_sst_time(config)
    sst_filename = get_sst_filename(config)
    vtable_sst   = wps_dir+'/ungrib/Variable_Tables/'+config['sst_vtable']
    vtable_dom   = wps_dir+'/ungrib/Variable_Tables/'+config['vtable']
    vtable       = wps_dir+'/Vtable'

    namelist_wps  = wps_dir+'/namelist.wps'
    namelist_dom  = '%s/%s/namelist.wps' % (domain_dir, model_run) 
    namelist_sst  = '%s/%s/namelist.sst' % (domain_dir, model_run)
    namelist      = read_namelist(namelist_dom)

    #
    # update one line to point to the new SST field
    # ungrib.exe will name SST field as e.g.
    # SST:2013-04-24_00
    #
    constants_name = '%s/SST:%s' %(wps_dir, sst_time.strftime('%Y-%m-%d_%H'))
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
    if os.path.exists(namelist_wps): os.remove(namelist_wps)

    # link namelist.sst to namelist.wps in WPS dir
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
    cmd     =  '%s/ungrib.exe' % wps_dir
    mpirun(cmd, 1, config['host_file'], config['run_level'], config['cmd_timing']) 


    cmd = 'grep "Successful completion" ./ungrib.log' # check for success
    ret = run_cmd(cmd, config)
    if ret!=0:
        raise IOError('Ungrib failed for SST')
    logger.info('*** SUCCESS UNGRIB SST ***')
    logger.debug('Removing namelist.wps')
    os.remove(namelist_wps)
    # link in original (unmodified) namelist.wps
    cmd = 'ln -sf %s %s' %(namelist_dom, namelist_wps)    
    run_cmd(cmd, config)
   
    
def prepare_wps(config):
    """ Runs all the pre-processing steps necessary for running WPS.
    
    Reads the current value of init_time from config, and links 
    boundary condition files into correct directory. Creates an output
    directory for the met_em files.
    
    Arguments:
    config -- dictionary containing various configuration options"""
    
    logger       = get_logger()
    logger.debug('*** PREPARING FILES FOR WPS ***')
    
    wps_dir      = config['wps_dir']
    domain_dir   = config['domain_dir']
    model_run    = config['model_run']
    init_time    = config['init_time']
    vtable       = config['vtable']

        
    #
    # link namelist.wps file from domain dir to 
    # wps dir. Fist check it exists
    #
    namelist_dom = '%s/%s/namelist.wps' % (domain_dir, model_run) 
    namelist_wps = wps_dir   +'/namelist.wps'

    #
    # Check a namelist exists in domain directory
    #    
    if not os.path.exists(namelist_dom):
        raise IOError('could not find namelist.wps file: %s' % namelist_dom)
        
    if os.path.exists(namelist_wps):
        logger.debug('removing existing namelist.wps file: %s' % namelist_wps)
        os.remove(namelist_wps)
    
    #
    #
    # Execute this command even in a dummy run, so that namelist file is linked
    # correctly and can be updated by other commands
    #
    cmd = 'ln -sf %s %s ' %(namelist_dom, namelist_wps)
    logger.debug(cmd)
    subprocess.call(cmd, shell=True)
        
    
    #
    # Link the correct Vtable into the WPS directory
    #
    vtab_path = wps_dir+'/ungrib/Variable_Tables/'+vtable
    vtab_wps  = wps_dir+'/Vtable'
    if os.path.exists(vtab_wps):
        os.remove(vtab_wps)
    cmd = 'ln -sf %s %s' %(vtab_path, vtab_wps)
    logger.debug(cmd)
    subprocess.call(cmd, shell=True)    
    
    #
    # Generate filelist based on the initial time, and the forecast hour
    #        
    filelist = get_bdy_filenames(config)

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
    os.chdir(wps_dir)
    args = ' '.join(filelist)
    cmd = '%s/link_grib.csh %s' %(wps_dir,args)
    run_cmd(cmd, config)
    
    #
    # Create a met_em directory based on the initial time.
    #
    met_em_dir = '%s/met_em/%s' %(domain_dir, init_time.strftime('%Y-%m-%d_%H'))
    logger.debug('Path for met_em files is %s' % met_em_dir)
    if not os.path.exists(met_em_dir):
        os.makedirs(met_em_dir)

    config['met_em_dir'] = met_em_dir
    
    logger.debug('*** FINISHED PREPARING FILES FOR WPS ***')    
    return 0




def update_namelist_wps(config):
    """ Updates the namelist.wps to reflect updated settings in config
    
    Arguments:
    config -- dictionary containing various configuration options
        
    """    
    logger     = get_logger()
    logger.debug('*** UPDATING namelist.wps ***')

    domain_dir = config['domain_dir']
    model_run  = config['model_run']
    wps_dir    = config['wps_dir']
    bdy_times  = get_bdy_times(config)
    max_dom    = config['max_dom']
    init_time  = config['init_time']
    met_em_dir = config['met_em_dir']
    geo_em_dir = '%s/geo_em' % domain_dir
    bdy_interval = config['bdy_interval']
    interval_seconds = bdy_interval * 60 * 60
    bdy_conditions = config['bdy_conditions'] 

    #
    # Read the namelist from model run directory
    #
    namelist_dom = '%s/%s/namelist.wps' %(domain_dir, model_run)
    logger.debug('reading namelist.wps <--------- %s' % namelist_dom)
    namelist = read_namelist(wps_dir+'/namelist.wps')
    
    #
    # Update some options based on the forecast config file
    #
    namelist.update('max_dom', max_dom)
    namelist.update('opt_output_from_metgrid_path', met_em_dir, section='metgrid')
    namelist.update('opt_output_from_geogrid_path', geo_em_dir, section='share')
    namelist.update('interval_seconds', [interval_seconds])
    namelist.update('prefix', bdy_conditions)   
    namelist.update('fg_name', bdy_conditions) 
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
    namelist.to_file(namelist_dom)
    logger.debug('*** FINISHED UPDATING namelist.wps ***')



def run_ungrib(config):
    """ Runs ungrib.exe and checks output was sucessfull
    
    Arguments:
    config -- dictionary specifying configuration options
    
    """
    logger          = get_logger()
    logger.info("*** RUNNING UNGRIB ***")
    
    
    wps_dir = config['wps_dir']
    os.chdir(wps_dir)
    
    namelist_wps = read_namelist('%s/namelist.wps' % wps_dir)
    #logger.debug('Contents of namelist.wps: ')
    #logger.debug(str(namelist_wps))
    cmd = 'rm -f ungrib.log'                             # remove any pre-existing log file
    run_cmd(cmd, config)
    
    #
    # Override some settings, only run ungrib with 1 processor
    #
    #settings = {'num_procs':1, 'mpi_cmd':config['mpi_cmd'],'host_file':config['host_file']}
    #mpi_cmd  = config['mpi_cmd']  % settings             # subsitute values into mpi command

    cmd     =  '%s/ungrib.exe' % wps_dir
    mpirun(cmd, 1, config['host_file'], config['run_level'], config['cmd_timing'])
    
    #run_cmd(cmd, config)


    cmd = 'grep "Successful completion" ./ungrib.log' # check for success
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
    wps_dir    = config['wps_dir']
    domain_dir = config['domain_dir']

    geogrid_dom = '%(domain_dir)s/%(model_run)s/GEOGRID.TBL' % config
    geogrid_wps = '%(wps_dir)s/GEOGRID.TBL' % config

    logger.debug("Linking GEOGRID.TBL into WPS dir")
    if not os.path.exists(geogrid_dom):
        raise IOError("Could not find GEOGRID.TBL at: %s " % geogrid_dom)
    
    if os.path.exists(geogrid_wps):
        os.remove(geogrid_wps)
    
    cmd = "ln -sf %s %s" %(geogrid_dom, geogrid_wps)
    run_cmd(cmd, config)

    cmd = 'rm -f %s/geogrid.log.*' % wps_dir
    run_cmd(cmd, config)
        
    #settings = {'num_procs':8, 'mpi_cmd':config['mpi_cmd'],'host_file':config['host_file']}
    #mpi_cmd  = config['mpi_cmd']  % settings             # subsitute values into mpi command
    cmd      =  '%s/geogrid.exe' % wps_dir
    
    mpirun(cmd, 8, config['host_file'], config['run_level'], config['cmd_timing'])
    #run_cmd(cmd, config)
    
    cmd = 'grep "Successful completion" %s/geogrid.log.*' %(wps_dir)
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
    
    wps_dir    = config['wps_dir']
    cmd        = 'rm -f %s/metgrid.log.*' % wps_dir
    run_cmd(cmd, config)

    #settings = {'num_procs':8, 'mpi_cmd':config['mpi_cmd'],'host_file':config['host_file']}
    #mpi_cmd = config['mpi_cmd']  % settings             # subsitute values into mpi command
    cmd      =  "%s/metgrid.exe" % wps_dir
    mpirun(cmd, 8, config['host_file'], config['run_level'], config['cmd_timing'])


    cmd = 'grep "Successful completion" ./metgrid.log.*'
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
    
    domain_dir   = config['domain_dir']
    wrf_dir      = config['wrf_dir']
    wrf_run_dir  = wrf_dir+'/run'
    max_dom      = config['max_dom']
    domains      = range(1,max_dom+1)
    init_time    = config['init_time']
    fcst_hours   = config['fcst_hours']
    bdy_interval = config['bdy_interval']
    bdy_times    = get_bdy_times(config)
    met_em_dir   = '%s/met_em/%s' % (domain_dir, init_time.strftime('%Y-%m-%d_%H'))    
    met_em_files = ['%s/met_em.d%02d.%s.nc' % (met_em_dir,d, t.strftime(out_format)) for d in domains for t in bdy_times] 

        
    #
    # Clean up files from previous runs
    #        
    logger.debug('removing files from previous runs')
    os.chdir(wrf_run_dir)
    os.system("rm -f rsl.out.*")
    os.system("rm -f rsl.error.*")
    os.system("rm -f met_em.*")
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
        cmd = 'ln -sf %s ./'%f
        run_cmd(cmd, config)

    
    logger.debug('*** FINISHED PREPARING FILES FOR WRF ***')
    return 0



def update_namelist_input(config):    
    """ Updates the namelist.input file to reflect updated settings in config.
    Adds a non-standard &metadata section to give a name to the model run
    
    Arguments:
    config -- dictionary containing various configuration options
        
    """        
    logger = get_logger()        
    logger.debug('*** UPDATING namelist.input ***')
    
    domain_dir   = config['domain_dir']
    wrf_dir      = config['wrf_dir']
    model        = config['model']
    model_run    = config['model_run']
    domain       = config['domain']
    
    namelist_domain = '%s/%s/namelist.input'  %(domain_dir, model_run)
    namelist_run    = '%s/run/namelist.input' %wrf_dir
    namelist_wps    = '%s/%s/namelist.wps'  %(domain_dir, model_run)
    
    
    # read settings from domain-based namelist
    namelist        = read_namelist(namelist_domain)   

    # read settings from domain-based namelist.wps
    namelist_wps   = read_namelist(namelist_wps)   
    wps_settings    = namelist_wps.settings


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
    dfi_bck      = config['dfi_bck'] * minute
    dfi_fwd      = config['dfi_fwd'] * minute
    dfi_bckstop  = start - dfi_bck
    dfi_fwdstop  = start + dfi_fwd
    

    namelist.update('dfi_bckstop_year',   dfi_bckstop.year,   'dfi_control')
    namelist.update('dfi_bckstop_month',  dfi_bckstop.month,  'dfi_control')
    namelist.update('dfi_bckstop_day',    dfi_bckstop.day,    'dfi_control')
    namelist.update('dfi_bckstop_hour',   dfi_bckstop.hour,   'dfi_control')
    namelist.update('dfi_bckstop_minute', dfi_bckstop.minute, 'dfi_control')
    namelist.update('dfi_bckstop_second', dfi_bckstop.second, 'dfi_control')
    namelist.update('dfi_fwdstop_year',   dfi_fwdstop.year,   'dfi_control')
    namelist.update('dfi_fwdstop_month',  dfi_fwdstop.month,  'dfi_control')
    namelist.update('dfi_fwdstop_day',    dfi_fwdstop.day,    'dfi_control')
    namelist.update('dfi_fwdstop_hour',   dfi_fwdstop.hour,   'dfi_control')
    namelist.update('dfi_fwdstop_minute', dfi_fwdstop.minute, 'dfi_control')
    namelist.update('dfi_fwdstop_second', dfi_fwdstop.second, 'dfi_control')


    #
    # Backup namelist.input.
    # Then change start and end dates to
    # match the year and month given to this script
    #
    logger.debug('copying namelist.input to namelist.input.backup')
    cmd = 'cp %s %s.backup' %(namelist_domain, namelist_domain)
    run_cmd(cmd, config)
    
    logger.debug('writing new settings to file')
    namelist.to_file(namelist_domain)
    
    logger.debug('linking namelist.input to WRF/run directory')
    cmd = 'rm -f %s' % namelist_run
    run_cmd(cmd, config)
    cmd = 'ln -sf %s %s' %(namelist_domain, namelist_run)
    run_cmd(cmd, config)

    #logger.debug(namelist)
    logger.debug('*** FINISHED UPDATING namelist.input ***')  
    return 0    

    
def run_real(config):
    """ Run real.exe and check output was sucessful
    Arguments:
    config -- dictionary containing various configuration options """
    
    logger = get_logger()    
    logger.info('*** RUNNING REAL ***')
    wrf_dir         = config['wrf_dir']
    wrf_run_dir     = wrf_dir+'/run' 
    wps_dir         = config['wps_dir']
    domain          = config['domain']
    domain_dir      = config['domain_dir']
    model_run       = config['model_run']
    init_time       = config['init_time']

    cmd     =  "%s/real.exe" % wrf_run_dir
    mpirun(cmd, 1, config['host_file'], config['run_level'], config['cmd_timing'])
    
    rsl = '%s/rsl.error.0000' % wrf_run_dir
    if not os.path.exists(rsl):
        raise IOError('No log file found for real.exe')

    # now copy rsl file to a log directory
    cmd = 'cp %s %s/rsl/rsl.error.%s.%s.%s' % (rsl, domain_dir, domain, model_run, init_time.strftime('%y-%m-%d_%H') )
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
    wrf_dir         = config['wrf_dir']
    num_procs       = config['num_procs']
    
    wrf_run_dir     = wrf_dir+'/run' 
    
    cmd   = '%s/wrf.exe' % wrf_run_dir
    mpirun(cmd, config['num_procs'], config['host_file'], config['run_level'], config['cmd_timing'])

    #
    # Check for success
    #    
    cmd = 'grep "SUCCESS COMPLETE" rsl.error.0000'
    ret =  run_cmd(cmd, config)
    if ret!=0:
        raise IOError('wrf.exe did not complete')
    
    logger.info('*** SUCESS WRF ***')


def move_wrfout_files(config):
    """ Moves output files to correct location for later processing
    with the UPP tool. Deprecated. Use archive instead.
    
    Arguments:
    config -- dictionary containing various configuration options
    
    """
    logger = get_logger()    
    logger.debug('*** MOVING WRFOUT FILES AND NAMELIST SETTINGS ***')
    
    domain        = config['domain']
    domain_dir    = config['domain_dir']
    wrf_run_dir   = config['wrf_dir']+'/run'
    model_run     = config['model_run']
    init_time     = config['init_time']
    init_str      = init_time.strftime('%Y-%m-%d_%H')
    
    
    wrfout_dir    = '%s/%s/wrfout' %(domain_dir, model_run)
    model_run_dir = '%s/%s'       %(domain_dir, model_run)
    log_dir       = '%s/log'      % model_run_dir    
    rsl_dir       = '%s/rsl'      % model_run_dir
    namelist_dir  = '%s/namelist' % model_run_dir
    run_key       = '%s.%s'              %(domain, model_run)    # composite key  

    logger.debug('Moving wrfout files to %s' % wrfout_dir)
    cmd           = 'mv %s/wrfout_d* %s' % (wrf_run_dir,wrfout_dir)
    run_cmd(cmd, config)
    
    #
    # Archive namelist files
    #
    
    if not os.path.exists(namelist_dir):
        os.makedirs(namelist_dir)
    
    
    cmd = 'cp %s/%s/namelist.input %s/namelist.input.%s.%s' % (domain_dir, model_run, namelist_dir, run_key, init_str)
    run_cmd(cmd, config)
    
    cmd = 'cp %s/%s/namelist.wps %s/namelist.wps.%s.%s' % (domain_dir, model_run, namelist_dir, run_key, init_str)
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
    wrf_run_dir   = config['wrf_dir']+'/run'
    model_run     = config['model_run']
    backup_base   = config['backup_dir']
    archive_mode   = config['archive_mode']
    backup_dirs   = config['backup_dirs']       # These are the directories to archive/backup
    
    model_run_dir    = '%s/%s'      %(domain_dir, model_run)
    model_run_backup = '%s/%s/%s'   %(backup_base, domain, model_run)
  
    
    wrfout_dir    = '%s/wrfout'        % model_run_dir
    wrfpost_dir   = '%s/wrfpost'       % model_run_dir
    log_dir       = '%s/log'           % model_run_dir
    rsl_dir       = '%s/rsl'           % model_run_dir
    namelist_dir  = '%s/namelist'      % model_run_dir

    for bd in backup_dirs:
        logger.debug('archiving files in %s' % bd)
        #
        # Remember the trailing slash!
        #
        source = '%s/%s/' % (model_run_dir, bd)
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
    wrf_run_dir   = config['wrf_dir']+'/run'
    model_run     = config['model_run']
    backup_dir    = config['backup_dir']
    wrfout_dir    = '%s/%s/wrfout' %(domain_dir, model_run)
    model_run_dir = '%s/%s'   %(domain_dir, model_run)
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
    model_run_dir = '%s/%s'   %(domain_dir, model_run)
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
    wrf_run_dir   = config['wrf_dir']+'/run'
    namelist      = read_namelist(wrf_run_dir+'/namelist.input')

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
    os.chdir(post_dir)

    #
    # Clean up old output files
    #
    logger.debug('Removing old output files')
    cmd = 'rm -f %s/*.out' % post_dir
    run_cmd(cmd, config)
    cmd = 'rm -f %s/*.tm00' % post_dir
    run_cmd(cmd, config)
    
    
    # Link Ferrier's microphysic's table and Unipost control file, 
    cmd = 'ln -sf %s/ETAMPNEW_DATA ./eta_micro_lookup.dat' % wrf_run_dir
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
    # In the wrf_run_dir
    #
    logger = get_logger()
    logger.info('*** Computing timing information ***')
    wrf_dir        = config['wrf_dir']
    rsl_file       = '%s/run/rsl.error.0000'%wrf_dir
    namelist_input = '%s/run/namelist.input' % wrf_dir
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

    cleanup_dir = config['cleanup_dirs']
    for d in cleanup_dir:
        cmd = 'rm -f %s' % d
        run_cmd(cmd, config)


#
#
#    domain_dir    = config['domain_dir']
#    model_run     = config['model_run']
#    init_time     = config['init_time']
#    remove_wrfout = config['remove_wrfout']
#    remove_met_em = config['remove_met_em']
#    remove_wps    = config['remove_wps']
#    
#    init_str      = init_time.strftime('%Y-%m-%d_%H')
#    met_em_dir    = '%s/met_em/%s' % (domain_dir, init_str)   
#    wps_dir       = config['wps_dir']
#    tmp_dir       = config['tmp_dir']
#       
#    if remove_met_em:
#        logger.debug("removing met_em directory")
#        cmd = 'rm -r -f %s ' % met_em_dir
#        run_cmd(cmd, config)
#    
#    #
#    # Remove old WPS files. FILE is hard-coded.
#    #
#    if remove_wps:
#        #cmd = 'find %s -type f -name "FILE*" -mtime +3 -exec rm -f {} \;' % wps_dir
#        cmd = 'rm -f %s/FILE*' % wps_dir
#        run_cmd(cmd, config) 
#        cmd = 'rm -f %s/GFS*' % wps_dir#
#	run_cmd(cmd,config)
#        cmd = 'rm -f %s/PFILE*' % wps_dir
#       run_cmd(cmd,config)
#        cmd = 'rm -f %s/geogrid.log.* %s/metgrid.log.*' % (wps_dir, wps_dir)
#        run_cmd(cmd, config) 
#                
#    #
    # Remove wrfout netcdf files if told to
    #
#    if remove_wrfout:
#        wrfout = '%s/%s/wrfout_*_%s*' % (domain_dir, model_run, init_str)
#        logger.debug('removing wrfout netcdf files')
#        cmd = 'rm -f %s' %wrfout
#        run_cmd(cmd, config)
#        
    logger.info('*** FINISHED CLEANUP ***')
#    return 0
