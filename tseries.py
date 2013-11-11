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
import powercurve
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
    logger.debug(frame)
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
    model_run   = config['model_run']
    init_time   = config['init_time']
    tseries_dir = '%s/%s/tseries' % (domain_dir, model_run)
    json_dir    = '%s/%s/json' % (domain_dir, model_run)
    json_file   = '%s/fcst_data.json' % json_dir

    logger.debug('json_dir: %s ' %json_dir)

    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
    

    logger.info('*** CONVERTING TIME SERIES TO JSON ***')
    pattern = '%s/*%s*.txt' % (tseries_dir, init_time.strftime('%Y-%m-%d_%H'))
    logger.debug(pattern)
    infiles = glob.glob(pattern)
    if len(infiles)==0:
        raise IOError('could not find any time-series files to process')    

    logger.debug('Found %d time-series files to process' % len(infiles))
    for n,f in enumerate(infiles):
        if n==0:
            frame = pd.read_csv(f, parse_dates=[8,9])
        else:
            new_frame =  pd.read_csv(f, parse_dates=[8,9])
            frame = pd.concat((frame,new_frame))

    jstring = to_json(frame)
    f = open(json_file, 'w')
    f.write(jstring)
    f.close()
   
    logger.info('*** WRITTEN JSON DATA ***')

def json_to_web(config):
    logger = wrftools.get_logger()

    model_run_dir = config['model_run_dir']
    init_time   = config['init_time']
    json_dir    = '%s/json' % model_run_dir
    json_files   =  glob.glob('%s/*.json' % json_dir)
    json_web_dir     = wrftools.sub_date(config['json_web_dir'], init_time)
    
    logger.info('*** COPYING JSON TO WEB DIR ***')
    
    wrftools.transfer(json_files,json_web_dir, mode='copy', debug_level='NONE')
    logger.info('*** COPIED JSON DATA ***')


def extract_tseries(config):

    logger = wrftools.get_logger()
    logger.info('*** EXTRACTING TIME SERIES ***')
     
    wrfout_dir     = config['wrfout_dir']
    tseries_dir    = config['tseries_dir']
    init_time      = config['init_time']
    dom            = config['dom']
    fcst_file      = '%s/wrfout_d%02d_%s:00:00.nc' %(wrfout_dir, dom, init_time.strftime("%Y-%m-%d_%H")) # note we add on the nc extension here
    loc_file       = config['locations_file']
    ncl_code       = config['tseries_code']
    tseries_fmt    = config['tseries_fmt']
    
    ncl_log        = config['ncl_log']
    if not os.path.exists(tseries_dir):
        os.makedirs(tseries_dir)
    
    # Always go via the netcdf file
    tseries_file = '%s/tseries_d%02d_%s.nc' % (tseries_dir, dom,init_time.strftime("%Y-%m-%d_%H"))

    os.environ['FCST_FILE']      = fcst_file
    os.environ['LOCATIONS_FILE'] = loc_file
    os.environ['NCL_OUT_DIR']    = tseries_dir
    os.environ['NCL_OUT_FILE']   = tseries_file

    logger.debug('Setting environment variables')
    logger.debug('FCST_FILE    ----> %s'  % fcst_file)
    logger.debug('NCL_OUT_DIR  ----> %s'  % tseries_dir)
    logger.debug('NCL_OUT_FILE  ----> %s' % tseries_file)


    for script in ncl_code:
        cmd  = "ncl %s >> %s 2>&1" % (script, ncl_log)
        wrftools.run_cmd(cmd, config)


    if 'txt' in tseries_fmt:
        ncdump.write_seperate_files([tseries_file], tseries_dir)
    
    if 'json' in tseries_fmt:
        ncdump.write_json_files_loc([tseries_file], ncdump.GLOBAL_ATTS, ncdump.VAR_ATTS,ncdump.COORD_VARS, tseries_dir, ncdump.FILE_DATE_FMT)        


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




def power(config):
    """Reads 'time series' file written by wgrib2. Creates arrays of U, V,
    and derives speed and direction. Loads power curve and converts to power. 
    
    Currently the fcst_tseries  is defined as:
      rowid integer
      domain text,
      model_run text,
      model text,
      grid_id integer,
      fcst_lead double precision,
      fcst_valid timestamp without time zone,
      fcst_init timestamp without time zone,
      fcst_var text,
      obs_sid text,
      fcst_lat double precision,
      fcst_lon double precision,
      fcst_elv double precision,
      fcst double precision,
      climo double precision"""
    
        
    #
    # TODO 
    #
    # Really, the writing to and reading from disk of time series could be saved by using a pipe
    # but let's use this method for now as the string parsing will be the same anyway
    #
    logger          = wrftools.get_logger()
    domain          = config['domain']
    domain_dir      = config['domain_dir']
    model           = config['model']
    model_run       = config['model_run']
    dom             = config['dom']
    init_time       = config['init_time']
    locations_file  = config['locations_file']
    pcurve_dir      = config['pcurve_dir']
    locations       = io._read_locations(locations_file)

    ts_dir          = '%s/%s/tseries' % (domain_dir, model_run)
    
    
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # Remember - grid winds are not rotated to earth winds yet
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    for park in locations:
        try:
            name      = park['name']
            lat       = park['lat']
            lon       = park['lon']
            hgt_col = park['hgt']
            var_col  = park['vars']
            if hgt_col=='-' or var_col=='-':
                logger.debug("No time series requested for %s, skipping " % name)
                continue
            hgts      = park['hgt'].strip().split(':')
            var_names = park['vars'].strip().split(':')
            if not 'POWER' in var_names:
                logger.debug("No power predictions series requested for %s, skipping " % name)
                continue
            
            
            logger.info('Predicting power output for %s' % name )
        
           
            for hgt in hgts:
                #u_file        = '%s/%s_%s_d%02d_%s_%s.txt' %(ts_dir, name, 'UGRD', dom,  hgt, init_time.strftime('%Y-%m-%d_%H'))
                #v_file        = '%s/%s_%s_d%02d_%s_%s.txt' %(ts_dir, name, 'VGRD', dom,  hgt, init_time.strftime('%Y-%m-%d_%H'))
                #u_series    = _read_time_series(u_file)
                #v_series    = _read_time_series(v_file)
                
                
                spd_file = '%s/%s_%s_d%02d_%s_%s.txt' %(ts_dir, name, 'SPEED', dom,  hgt, init_time.strftime('%Y-%m-%d_%H'))
                dir_file = '%s/%s_%s_d%02d_%s_%s.txt' %(ts_dir, name, 'DIRECTION', dom,  hgt, init_time.strftime('%Y-%m-%d_%H'))
                spd_series  = _read_time_series(spd_file)
                dir_series  = _read_time_series(dir_file)
                
                speed     = spd_series['val']
                direction = dir_series['val']
                
                times_spd   = spd_series['valid_time']
                init_times  = spd_series['init_time']
            
                #
                # Create a 'time series' object. Maybe we don't need to create this
                # but will offer us flexibility later.
                #
                tseries =  {'FCST_VALID': np.array(times_spd), 'SPEED': np.array(speed), 'DIRECTION': np.array(direction)}
              
                #
                # Open power curve
                #
                pcurve = powercurve.from_file('%s/%s.csv' %(pcurve_dir, name))
        
                
                #
                # TODO: due to the way scipy interpolate works
                # the x and y data must be monotonic
                #
                # To get around this, we just loop over each speed, direction
                # pretty slow, so we should change
                #
                pwr = np.zeros(speed.shape[0])
                for n in range(speed.shape[0]):
                    pwr[n] = pcurve.power(speed[n], direction[n]) 
                    #logger.debug('%0.2f  %0.2f  %0.2f' %(speed[n], direction[n], pwr[n]))
                
                tseries['POWER'] = pwr
        
        
                #
                # Write the power to a time series as well
                # this will be a slightly different format,
                # but no matter
                # 
                pwr   = tseries['POWER']
                times = tseries['FCST_VALID']
                
                
                #
                # We want this to be a record-based format, mimicking the the mpr format output from
                # met so we can use the same visualisation and error tools
                #
                out_name = '%s/%s_%s_d%02d_%s_%s.txt' %(ts_dir, name, 'POWER',dom, hgt, init_time.strftime('%Y-%m-%d_%H'))
                out_file = open(out_name, 'w')
                for n in range(times.shape[0]):
                    valid_time = times[n]
                    delta      = valid_time - init_time  
                    fhr        =  ((delta.days*24*60*60) + delta.seconds)/3600
                    value      = pwr[n]
                    line       = '%s,%s,%s,%02d,%s,%s,%s,%s,%s,%s,%s,%s\n' %(domain, 
                                                                          model,
                                                                          model_run, 
                                                                          dom, 
                                                                          init_time, 
                                                                          valid_time, 
                                                                          'POWER',
                                                                          name,
                                                                          lat, 
                                                                          lon, 
                                                                          hgt,
                                                                          value)
                    
                    out_file.write(line)
                    
            logger.info('finished %s' %name)            
        except IOError:
            wrftools.handle(config)




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






