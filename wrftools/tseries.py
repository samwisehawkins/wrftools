#************************************************************************
# tseries.py
# 
# Handles the extraction of time-series and the conversion to power
#
# TODO
# Split into two modules, one tseries, one power.
# Ensure power uses SPEED and DIRECTION rather than U and V
#
# names =  ['domain', 'model_run', 'model', 'grid_id', 'fhr', 'valid_time', 'init_time', 'var', 'obs_sid', 'lat', 'lon', 'hgt', 'val']
# Currently forecast tseries has the following column headings
#fcst_ts_names = ['domain', 'model', 'model_run', 'nest_id', 'fcst_init','fcst_valid', 'fcst_var',
#                 'location_id', 'fcst_lat', 'fcst_lon', 'fcst_hgt', 'fcst_val']
#
#
#************************************************************************
import os
import csv
import time, datetime
import numpy as np
import wrftools
import tools
from customexceptions import DomainError
import ncdump
import pandas as pd
import json
import glob

HOUR = datetime.timedelta(0, 60*60)                 


def to_json(frame):
    """ convert a pandas dataframe to json representation """
    frame = frame.set_index(['location_id','nest_id', 'variable', 'height'])
    logger=wrftools.get_logger()
    groupby = frame.index.names
    grouped = frame.groupby(level=groupby)
    ngroups = grouped.ngroups
    # as long as there is only one reference to a string
    # concatenation is O(n), so not too bad a method
    result = '['
    for i,(names, group) in enumerate(grouped):
        result += '{'
        for j,name in enumerate(names):
            result+='"%s":"%s"' % (groupby[j], name)
            if j<len(names):
                result+=',\n'
        ts     = [time.mktime(t.timetuple())*1000 for t in group.valid_time]
        values = group.value
        
        # This is a bit of a hack
        # Truncate values to 3 decimal places
        valstrs = ['%0.3f' % v for v in values]
        series = map(list, zip(ts,valstrs )) 
        result += '"data" : '
        
        # Because the values have been converted to 3-decimal place strings
        # They are enclosed in ' ', which we need to remove.
        result += str(series).replace("'", "")
        result += '}'
        if i<ngroups-1:
            result+=',\n'
    result+=']'
    result = result.replace('nan', 'null')
    result = result.replace("'", "")
    return result
    

    
    
def tseries_to_json(config):
    """Converts the time series, in the record-based format, to JSON strings for plotting """
    logger=wrftools.get_logger()
    
    domain_dir  = config['domain_dir']
    domain      = config['domain']
    dom         = config['dom']
    model_run   = config['model_run']
    init_time   = config['init_time']

    tseries_dir  = config['tseries_dir']
    tseries_file = '%s/tseries_d%02d_%s.nc' % (tseries_dir, dom,init_time.strftime("%Y-%m-%d_%H"))
    json_dir     = '%s/%s/json' % (domain_dir, model_run)
    #json_file    = '%s/fcst_data.json' % json_dir

    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
    
    ncdump.write_json_files([tseries_file], ncdump.GLOBAL_ATTS, ncdump.VAR_ATTS,ncdump.COORD_VARS, json_dir, ncdump.FILE_DATE_FMT)        
  
    logger.info('*** WRITTEN JSON DATA ***')




    
    #if 'aot' in tseries_fmt:
    #    ncdump.write_aot_files([tseries_file], tseries_dir)
    
    #if 'json' in tseries_fmt:
    #    ncdump.write_json_files([tseries_file], ncdump.GLOBAL_ATTS, ncdump.VAR_ATTS,ncdump.COORD_VARS, json_dir, ncdump.FILE_DATE_FMT)        

#*****************************************************************
# Read location files
#*****************************************************************

def _in_domain(lat, lon, lat2d, lon2d):
    """Tests whether (lat,lon) is within domain defined by lat2d and lon2d.
    Simply tests lat within lat2d and lon within lon2d
    Returns boolean, true if the point is within the domain """    

    logger = wrftools.get_logger()
    
    min_lon = np.min(lon2d)
    max_lon = np.max(lon2d)
    min_lat = np.min(lat2d)
    max_lat = np.max(lat2d)
    
    if (lat < min_lat) or (lat> max_lat) or (lon<min_lon) or (lon>max_lon):
          logger.debug("point (%0.3f, %0.3f) is not within domain (%0.2f, %0.3f, %0.3f, %0.3f)" %(lat, lon, min_lat, max_lat, min_lon, max_lon))
          return False
    else:
        return True
    

def _get_index(lat, lon, lat2d, lon2d):
    """ Finds the nearest mass point grid index to the point (lon, lat).
        Works but is slow as just naively searches through the arrays point
        by point. Would be much better to implement the ncl function 
        wrf_user_get_ij to use projection information to actually calculate
        the point in porjected space. 
        
        Arguments:
            @lat: the latitude of the target point
            @lon: longitude of the target point
            @lat2d: 2d array of latitudes of grid points
            @lon2d: 2d array of longitudes of grid points
            
       Returns (i,j) of nearest grid cell. Raises exception if outside"""

    logger = wrftools.get_logger()
    logger.debug("finding index of (%0.3f, %0.3f) " %(lat,lon))
    west_east   = lat2d.shape[0]
    south_north = lat2d.shape[1]    
    logger.debug("dimensions of domain are: %d south_north, %d west_east" %(south_north, west_east))
    
    if not _in_domain(lat, lon, lat2d, lon2d):
        logger.error('point (%0.3f, %0.3f) not in model domain' % (lat, lon))
        raise DomainError('point (%0.3f, %0.3f) not in model domain' %(lat, lon))
    
    
    
    # 
    # slow, but will work. Just search through the arrays until we 
    # hit the nearest grid point
    #
    min_dist = 10000000  # if the point is further than 10M m away, don't bother!
    min_x = 0
    min_y = 0 
    

    for x in range(west_east-1):
        for y in range(south_north-1):            
            point_lat = lat2d[x,y]
            point_lon = lon2d[x,y]
            
            d = tools.haversine(lat, lon, point_lat, point_lon)
            
            if d < min_dist:
                min_dist = d
                min_x = x
                min_y = y
    
    if min_x==0 or min_y==0 or min_x>west_east or min_y>south_north:
        logger.error("Point is on/off edge of of model domain, this should have been caught earlier!")
        raise DomainError("Point is on/off edge of of model domain")
        
        
    
    logger.debug('nearest grid index is x=%d, y=%d, %0.3f m away' %(min_x, min_y, min_dist))
    logger.debug('latitude, longitude of original is (%0.3f, %0.3f)' %(lat, lon))
    logger.debug('latitude, longitude of index is (%0.3f, %0.3f)' %(lat2d[min_x,min_y], lon2d[min_x,min_y]))
    
    return (min_x, min_y, min_dist)
    

def _expression(var_name):
    """Works out whether a variable definition is actually 
    an expression """
    #return '(' in var_name or '+' in var_name or '-' in var_name
    return '(' in var_name
    

def _read_time_series(fname):
    """ Reads formatted time series"""

    logger = wrftools.get_logger()
    logger.debug('reading tseries file %s' % fname)
    
    #
    # Current format of time series files is:
    #fcst_ts_names = ['domain', 'model', 'model_run', 'nest_id', 'fcst_init','fcst_valid', 'fcst_var',
    #                'location_id', 'fcst_lat', 'fcst_lon', 'fcst_hgt', 'fcst_val']
    #
    names =  ['domain', 'model', 'model_run', 'grid_id', 'init_time', 'valid_time', 'var', 'obs_sid', 'lat', 'lon', 'hgt', 'val']
    converters = {4: wrftools.strptime, 5: wrftools.strptime}
    
    rec = np.genfromtxt(fname, delimiter=',', names=names, dtype=None, converters=converters)
    return rec








#*************************************************************************
# Deprecated
# functions below here are marked for deletion
#*************************************************************************


def get_ij_old(config):
    logger = wrftools.get_logger()    
    logger.info('*** RUNNING NCL EXTRACTION ***')
     
    domain_dir    = config['domain_dir']
    model_run     = config['model_run']
    ncl_nc        = config['ncl_nc']
    ncl_grb       = config['ncl_grb']
    ncl_code_dir  = config['ncl_code_dir']
    ncl_nc_code   = config['ncl_nc_code']
    ncl_grb_code  = config['ncl_grb_code']
    
    wrfout_dir    = '%s/%s/'%(domain_dir, model_run)
    init_time     = config['init_time']
    dom           = config['dom']
    grb_file      = '%s/%s/archive/wrfpost_d%02d_%s.grb'    %(domain_dir, model_run, dom, init_time.strftime(archive_format))
    nc_file       = '%s/%s/wrfout/wrfout_d%02d_%s:00:00.nc' %(domain_dir, model_run, dom, init_time.strftime(archive_format))
    
    ncl_out_dir   = '%s/%s/plots/%s/d%02d/'              %(domain_dir,model_run, init_time.strftime(archive_format), dom)    
    ncl_output    = config['ncl_output']
    namelist_wps  = '%(domain_dir)s/%(model_run)s/namelist.wps' % config

    if not os.path.exists(ncl_out_dir):
        os.makedirs(ncl_out_dir)

    #
    # Communicate to NCL via environment variables
    #
    os.environ['DOMAIN_DIR']    = domain_dir
    os.environ['MODEL_RUN']     = model_run
    os.environ['NCL_OUT_DIR']   = ncl_out_dir
    os.environ['NCL_OUTPUT']    = ncl_output 
    os.environ['NAMELIST_WPS']  = namelist_wps
    os.environ['FCST_FILE']     = grb_file
    cmd    = "ncl %s/wrf_grib_series.ncl" % (ncl_code_dir)
    p      =  subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    lines  = p.stdout.readlines()
    for line in lines:
        if '(0,0)' in line:
            thanet_i = line.split()[-1]
            logger.debug(thanet_i)
        if '(0,1)' in line:
            aberdeen_i = line.split()[-1]
            logger.debug(aberdeen_i)
        if '(1,0)' in line:
            thanet_j = line.split()[-1]
            logger.debug(thanet_j)
        if '(1,1)' in line:
            aberdeen_j = line.split()[-1]
            logger.debug(aberdeen_j)
            
    return [(thanet_i, thanet_j), (aberdeen_i, abderdeen_j)]






