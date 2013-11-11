"""ncdump.py dumps data from a netcdf file to text file

Usage: 
    ncdump.py <file>... --format=<fmt> [--dims=<dimspec>]... [--out=<dir>] [-h | --help]
    
Options:
    --out=<dir>       output directory to write time-series
    --dims=<dimspec>  dimension specification of the form dimname,start,end
    --format=<fmt>    format for output, txt or json
    -h |--help        show this message
    
Notes:
    Currently the file format is fixed
    
Examples:

    python ncdump.py wrfout_d01_2010-01-* --out=./tseries """

import sys
import docopt
import subprocess
import time
import datetime
from netCDF4 import Dataset
from netCDF4 import num2date, date2num
import wrftools
import json

COORD_VARS      = ['time', 'height', 'location', 'lat', 'lon']
FILE_DATE_FMT   = '%Y-%m-%d_%H%M'  # Date format for file name
DATE_FMT        = '%Y-%m-%d %H:%M' # Date format within files
GLOBAL_ATTS     = ['DOMAIN', 'MODEL_RUN', 'GRID_ID']  # which global attributes to copy from ncfile to json
VAR_ATTS        = ['units', 'description']  # which variables attributes to include in json series
FULL_SLICE      = {'time': (0,None), 'location': (0,None), 'height':(0,None)} # this represents no slicing

def main():         
    """ Pass command line arguments to NCL script"""
    args = docopt.docopt(__doc__, sys.argv[1:])

    print '\n********************************'
    print 'dumping netCDF time series to flat files'
    ncfiles = args['<file>']
    
    if args['--out']==None:
        out_dir = '.'
    else:
        out_dir = args['--out']

    dims = args['--dims']
    # time, location and height start and end indices
    # default is whole range
    ts = 0
    te = None
    ls = 0
    le = None
    hs = 0
    he = None
    
    if dims!=None:
        for dim in dims:
            d,s,e = dim.split(',')
            if d=='time':
                ts = int(s)
                te = int(e)
            if d=='location':
                ls = int(s)
                le = int(e)
            if d=='height':
                hs = int(s)
                he = int(e)

    dimspec = {'time': (ts, te), 'location':(ls, le), 'height': (hs, he)}

    if args['--format']=='txt':
        write_seperate_files(ncfiles, out_dir, dims)
    
    elif args['--format']=='json':
        write_json_files(ncfiles, GLOBAL_ATTS, VAR_ATTS,COORD_VARS,out_dir, FILE_DATE_FMT, dimspec)
    else:
        print 'format not understood'
        
def write_columns(ncfiles, fname):
    """Writes each variable and height into a seperate column"""
    pass
    
    
def write_seperate_files(ncfiles, out_dir, dims=None):        
    """ Writes each variable and height into a seperate text file"""

    logger = wrftools.get_logger()
    # time, location and height start and end indices
    ts = 0
    te = None
    ls = 0
    le = None
    hs = 0
    he = None
    
    if dims!=None:
        for dim in dims:
            d,s,e = dim.split(',')
            if d=='time':
                ts = int(s)
                te = int(e)
            if d=='location':
                ls = int(s)
                le = int(e)
            if d=='height':
                hs = int(s)
                he = int(e)
    

    for f in ncfiles:
        logger.debug('dumping netcdf time series to flat files')
        
        dataset = Dataset(f, 'r')
        # get some global attributes
        #model     = dataset.MODEL
        #nest_id   = dataset.GRID_ID
        #model_run = dataset.MODEL_RUN
        #domain    = dataset.DOMAIN
        
        logger.warn('Remove Aberdeen hack')
        model= 'WRF'
        nest_id  = dataset.GRID_ID
        model_run = 'resource'
        domain = 'aberdeen'
        #
        #
        logger.debug('model run is ' + model_run)
        
        
        variables     = dataset.variables
        fulltime      = variables['time']
        fulldatetimes = num2date(fulltime,units=fulltime.units,calendar=fulltime.calendar)
        
        time      = fulltime[ts:te]
        datetimes = fulldatetimes[ts:te]
        
        init_time = fulldatetimes[0]
        location  = variables['location'][ls:le]
        height    = variables['height']

        
        lat       = variables['lat'][ls:le]
        lon       = variables['lon'][ls:le]
        
        ntimes    = len(time)
        nlocs     = location.shape[0]
        loc_str_len = location.shape[1]
        

        for v in variables:
            # skip coordinate variables
            if v in COORD_VARS:
                continue
            print v
            
            fullvar = variables[v]
            print fullvar
            ndims = len(fullvar.shape)
            
            # 2D variable, variable[time, location]
            if ndims==2:
                var = fullvar[ls:le, ts:te]
            
            if ndims==3:
                var = fullvar[ls:le, hs:he, ts:te]
            
            
            for l in range(nlocs):
                loc = ''.join(location[l,0:loc_str_len])
                loc = loc.strip()
                
                # 2D variable
                if ndims==2:
                    hgts = [0.0]
                # 3D variable
                elif ndims==3:
                    hgts = height[hs:he]
                
                    
                for h in range(len(hgts)):
                    hgt = hgts[h]
                    fname = '%s/%s_%s_d%02d_%03d_%s.txt' % (out_dir, loc, v, nest_id, int(hgt), init_time.strftime(FILE_DATE_FMT))
                    fout = open(fname, 'w')
                    fout.write('domain,model_run,model,nest_id,location_id,latitude,longitude,variable,init_time,valid_time,height,value\n')
                    for t in range(ntimes):
                        valid_time = datetimes[t].strftime(DATE_FMT)
                        if ndims==2:
                            val = var[l,t]
                        elif ndims==3:
                            val = var[l,h,t]
                        line = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%03d,%0.3f\n' %(domain, model_run, model,nest_id,loc, lat[l], lon[l], v, init_time.strftime(DATE_FMT), valid_time, hgt, val)
                        fout.write(line)
        
                    fout.close()
        
        dataset.close()

        
        
def write_json_files(ncfiles, global_atts, var_atts,coord_vars, out_dir, file_date_fmt, dimspec=FULL_SLICE):        
    """ Writes each series into a separate json file
    
    Arguments
        @ncfiles     -- list of netcdf file names to extract data from
        @global_atts -- list of global attribute names in the nc files to copy to json series
        @var_atts    -- list of variables attributes to copy to json series
        @coord_vars  -- list of variables considered coordinate variables and not output as a series
        @out_dir     -- output directory to write files to
        @file_date_fmt -- date format to use in file naming
        @dims          -- dimension specification used so slice output variables"""

    logger = wrftools.get_logger()
    
    ts,te = dimspec['time']
    ls,le = dimspec['location']
    hs,he = dimspec['height']

    for f in ncfiles:
        logger.debug(f)
        logger.debug('dumping netcdf time series to json files')
        
        dataset = Dataset(f, 'r')
        # get some global attributes used for file naming
        model     = dataset.MODEL
        nest_id   = dataset.GRID_ID
        model_run = dataset.MODEL_RUN
        domain    = dataset.DOMAIN
        
        # Get subset of global attributes into a dictionary
        global_att_dict = dict([(att,dataset.getncattr(att)) for att in global_atts])
        
        variables     = dataset.variables
        fulltime      = variables['time']
        # convert to datetime objects
        fulldatetimes = num2date(fulltime,units=fulltime.units,calendar=fulltime.calendar)
        
        # subset time dimension
        times     = fulltime[ts:te]
        datetimes = fulldatetimes[ts:te]
        init_time = fulldatetimes[0]
        
        # For highcharts plotting, time must be in milliseconds since unix epoch
        timestamps      = [time.mktime(t.timetuple())*1000 for t in datetimes]
        init_timestamp = time.mktime(init_time.timetuple())*1000 

        # subset locations if asked
        location  = variables['location'][ls:le]
        height    = variables['height']

        lat       = variables['lat'][ls:le]
        lon       = variables['lon'][ls:le]
        
        ntimes    = len(times)
        nlocs     = location.shape[0]
        loc_str_len = location.shape[1]
        
        # For each variable in the file
        for v in variables:
            print '\n\n\n************************************************'
            print 'processing %s ' % v
            # skip coordinate variables
            if v in coord_vars:
                continue
            
            fullvar = variables[v]
            ndims   = len(fullvar.shape)

            
            # 2D variable, variable[time, location]
            if ndims==2:
                var = fullvar[ts:te, ls:le]
            
            if ndims==3:
                print 'ts,te', ts,te
                #print ls,le
                #print hs,he
                var = fullvar[ts:te, ls:le, hs:he]

            
            var_att_dict = dict([(att,fullvar.getncattr(att)) for att in var_atts])
            series_dict = dict(global_att_dict.items()+ var_att_dict.items())
            
            
            for l in range(nlocs):
                loc = ''.join(location[l,0:loc_str_len])
                loc = loc.strip()
                
                # 2D variable
                if ndims==2:
                    hgts = [0.0]
                # 3D variable
                elif ndims==3:
                    hgts = height[hs:he]
                
                for h in range(len(hgts)):
                    # note if variable is 2D, we still execute this loop once
                    # with height=0
                    if ndims==2:
                        values = var[l, :]
                    elif ndims==3:
                        values = var[l,h,:]
                    
                    hgt = hgts[h]
                    data = map(list, zip(timestamps,values )) 
                    series_dict['location_id'] = loc
                    series_dict['height'] = hgt
                    series_dict['data'] = data
                    s = str(series_dict)

                    # this is an ugly hack which could potentially lead to errors if " u'" occurs at the end of a string
                    s =  s.replace(" u'", " '")

                    
                    # change single quotes to double
                    s = s.replace("'", '"')

                    fname = '%s/%s_%s_d%02d_%03d_%s.json' % (out_dir, loc, v, nest_id, int(hgt), init_time.strftime(file_date_fmt))
                    fout = open(fname, 'w')
                    fout.write(s)
                    fout.close()
        
        dataset.close()        
        
def write_json_files_loc(ncfiles, global_atts, var_atts,coord_vars, out_dir, file_date_fmt, dimspec=FULL_SLICE):        
    """ Writes each series into a separate json file
    
    Arguments
        @ncfiles     -- list of netcdf file names to extract data from
        @global_atts -- list of global attribute names in the nc files to copy to json series
        @var_atts    -- list of variables attributes to copy to json series
        @coord_vars  -- list of variables considered coordinate variables and not output as a series
        @out_dir     -- output directory to write files to
        @file_date_fmt -- date format to use in file naming
        @dims          -- dimension specification used so slice output variables"""

    logger = wrftools.get_logger()
    
    ts,te = dimspec['time']
    ls,le = dimspec['location']
    hs,he = dimspec['height']

    for f in ncfiles:
        logger.debug(f)
        logger.debug('dumping netcdf time series to json files')
        
        dataset = Dataset(f, 'r')
        # get some global attributes used for file naming
        model     = dataset.MODEL
        nest_id   = dataset.GRID_ID
        model_run = dataset.MODEL_RUN
        domain    = dataset.DOMAIN
        
        # Get subset of global attributes into a dictionary
        global_att_dict = dict([(att,dataset.getncattr(att)) for att in global_atts])
        
        variables     = dataset.variables
        fulltime      = variables['time']
        # convert to datetime objects
        fulldatetimes = num2date(fulltime,units=fulltime.units,calendar=fulltime.calendar)
        
        # subset time dimension
        times     = fulltime[ts:te]
        datetimes = fulldatetimes[ts:te]
        init_time = fulldatetimes[0]
        
        # For highcharts plotting, time must be in milliseconds since unix epoch
        timestamps      = [time.mktime(t.timetuple())*1000 for t in datetimes]
        init_timestamp = time.mktime(init_time.timetuple())*1000 

        # subset locations if asked
        location  = variables['location'][ls:le]
        height    = variables['height']

        
        
        lat       = variables['lat'][ls:le]
        lon       = variables['lon'][ls:le]
        
        ntimes    = len(times)
        nlocs     = location.shape[0]
        nvars     = len(variables)
        
        loc_str_len = location.shape[1]
        

            
            
        for l in range(nlocs):
            loc = ''.join(location[l,0:loc_str_len])
            loc = loc.strip()

            print '\n\n\n************************************************'
            print loc

            fname = '%s/%s_d%02d_%s.json' % (out_dir, loc, nest_id, init_time.strftime(file_date_fmt))
            fout = open(fname, 'w')
            first=True
            fout.write('[')
            # For each variable in the file
            for v in range(nvars):
                varname = variables.keys()[v]

                print 'processing %s ' % varname
                # skip coordinate variables
                if varname in coord_vars:
                    continue
                
                fullvar = variables[varname]
                ndims   = len(fullvar.shape)
                
                # 2D variable, variable[time, location]
                if ndims==2:
                    var = fullvar[ts:te, ls:le]
                
                if ndims==3:
                    print 'ts,te', ts,te
                    #print ls,le
                    #print hs,he
                    var = fullvar[ts:te, ls:le, hs:he]

                
                var_att_dict = dict([(att,fullvar.getncattr(att)) for att in var_atts])
                series_dict = dict(global_att_dict.items()+ var_att_dict.items())
                
                
                # 2D variable
                if ndims==2:
                    hgts = [0.0]
                # 3D variable
                elif ndims==3:
                    hgts = height[hs:he]
                
                for h in range(len(hgts)):
                    # note if variable is 2D, we still execute this loop once
                    # with height=0
                    if ndims==2:
                        values = var[l, :]
                    elif ndims==3:
                        values = var[l,h,:]
                    
                    hgt = hgts[h]
                    data = map(list, zip(timestamps,values )) 
                    series_dict['location_id'] = loc
                    series_dict['height'] = hgt
                    series_dict['data'] = data
                    s = str(series_dict)

                    # this is an ugly hack which could potentially lead to errors if " u'" occurs at the end of a string
                    s =  s.replace(" u'", " '")

                    
                    # change single quotes to double
                    s = s.replace("'", '"')
                    
                    fout.write(s)
                    #end of height loop, write comma but not last time in loop
                    if h<len(hgts)-1:
                        fout.write(',\n')
                if v<nvars-1:
                    fout.write(',\n')
            
            fout.write(']')
            fout.close()
        
        dataset.close()        



        
        
        
    
if __name__ == '__main__':
    main()

