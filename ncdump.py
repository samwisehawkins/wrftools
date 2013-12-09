"""ncdump.py dumps data from a netcdf file to text file

Usage: 
    ncdump.py <file>... --format=<fmt> [--dims=<dimspec>] [--out=<dir>] [-h | --help]
    
Options:
    <file>            input files
    --format=<fmt>    format for output, txt or json
    --dims=<dimspec>  dimension specification of the form dimname,start,end
    --out=<dir>       output directory to write time-series
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
import pandas as pd
from collections import OrderedDict
import re
import numpy as np

COORD_VARS      = ['time', 'height', 'location', 'lat', 'lon', 'location_id']
FILE_DATE_FMT   = '%Y-%m-%d_%H%M'  # Date format for file name
DATE_FMT        = '%Y-%m-%d %H:%M' # Date format within files
GLOBAL_ATTS     = ['DOMAIN', 'MODEL_RUN', 'GRID_ID']  # which global attributes to copy from ncfile to json
VAR_ATTS        = ['units', 'description']  # which variables attributes to include in json series
FULL_SLICE      = {'time': (0,None), 'location': (0,None), 'height':(0,None)} # this represents no slicing
CSV_NAME        = 'tseries.csv'       
JSON_NAME       = 'fcst_data.json'

def main():         
    """Dump a netcdf time-series file to a textual representation"""
    args = docopt.docopt(__doc__, sys.argv[1:])

    print '\n********************************'
    print 'dumping netCDF time series to flat files'
    print 'format chosen: %s' % args['--format'] 
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
    
    elif args['--format']=='csv':
        write_csv_files(ncfiles, out_dir, dimspec)
    
    else:
        print 'format not understood'
        

        
        
def write_csv_files(ncfiles, out_dir, dimspec=FULL_SLICE):        
    """Writes each variable and height into a seperate column.  Columns will be labelled variable_height where height if formatted as %03d int(height)"""
    
    #
    # How do we name the output files? One per input file? Or concatenate them together in the same way as the json files?
    # Perhaps concatenation is the way to go? 
    #
    # A better way might be to build a pandas DataFrame first, and then write it to  csv file
    #
    # Efficiency considerations. The current method sucks.  It makes more sense to try and load as 
    # much data into memory as possible. Currently, the time-series netcdf files are written out with 
    # location as the record dimension. This means they can't be concantenated over time very easily.
    #
    # It might make more sense to make time the record dimension, then concatenate (or use a MFDataset)
    # Then we could eliminate one of the file reading loops.
    #
    # It would bugger up other code though
    #
    
    logger = wrftools.get_logger()
    ts,te = dimspec['time']
    ls,le = dimspec['location']
    hs,he = dimspec['height']

    rows = []    

    for f in ncfiles:
        logger.debug('dumping netcdf time series to cvs columns')
        dataset = Dataset(f, 'r')
        # get some global attributes

        model     = dataset.MODEL
        nest_id   = dataset.GRID_ID
        model_run = dataset.MODEL_RUN
        domain    = dataset.DOMAIN
        
        variables     = dataset.variables

        fulltime      = variables['time']
        fulldatetimes = num2date(fulltime,units=fulltime.units,calendar=fulltime.calendar)
        
        time      = fulltime[ts:te]
        datetimes = fulldatetimes[ts:te]
        ntime     = len(datetimes) 
        init_time = fulldatetimes[0]
      
        location    = variables['location'][ls:le]
        nloc        = location.shape[0]
        loc_id      = [''.join(location[l,0:-1]) for l in range(nloc)]
        
        height    = variables['height'][hs:he]
        nheight   = len(height)

        # this will force the reading all of the required variable data into memory
        varnames = [v for v in variables if v not in COORD_VARS]
        vardata  = dict([(v, variables[v][:]) for v in varnames])

        for t in range(ntime):
            for l in range(nloc):
                rowdict = OrderedDict()
                rowdict['valid_time']  = datetimes[t]
                rowdict['location_id'] = loc_id[l]
                rowdict['init_time']   = init_time

                for v in varnames:
                    data = vardata[v]
                    print v, data.shape
                    
                    # 2D variable
                    if len(data.shape)==2:
                        rowdict[v] = data[t,l]
                    
                    # 3D variable
                    if len(data.shape)==3:
                        for h in range(nheight):
                            key = '%s_%03d' %(v, int(height[h]))
                            rowdict[key] = data[t,l,h]
                        
                rows.append(rowdict)
        dataset.close()
    
    df       = pd.DataFrame(rows)
    cols     = list(df.columns)


    
    # change the order of columns 
    #var_cols = cols[2:]

    pre_cols = ['init_time','valid_time','location_id']
    data_cols = [c for c in cols if c not in pre_cols]
    print pre_cols
    print data_cols
    new_cols = pre_cols + data_cols
    
    #
    #pre_cols[0] = 'init_time'
    #pre_cols[1] = 'valid_time'
    #pre_cols[2] = 'location_id'
    #
    df = df[new_cols]
    df.to_csv('%s/%s' % (out_dir, CSV_NAME), index=False, float_format='%0.3f')
    #print df.to_string()
    
    
    
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
        model     = dataset.MODEL
        nest_id   = dataset.GRID_ID
        model_run = dataset.MODEL_RUN
        domain    = dataset.DOMAIN
        
        #logger.warn('Remove Aberdeen hack')
        #model= 'WRF'
        #nest_id  = dataset.GRID_ID
        #model_run = 'resource'
        #domain = 'aberdeen'
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
    """ Writes each series into one json file
    
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
        
        
        # start of the json file
        # fout.write('[')
        series = []    
            
        for l in range(nlocs):
            loc = ''.join(location[l,0:loc_str_len-1])
            loc = loc.strip()
   
            
            #fname = '%s/%s_d%02d_%s.json' % (out_dir, loc, nest_id, init_time.strftime(file_date_fmt))
            #logger.debug('writing json to %s'  % fname)
            #fout = open(fname, 'w')
            #first=True
            #fout.write('[')
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

                print var_atts
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
                        values = np.ma.array(var[:,l])
                    elif ndims==3:
                        values = np.ma.array(var[:,l,h])
                    
                    hgt = hgts[h]
                    # encode with 3 decimal places
                    #valstrs = ['%0.3f' % v for v in values]
                    data = map(list, zip(timestamps,values )) 
                    series_dict['variable'] = varname
                    series_dict['location_id'] = loc
                    series_dict['height'] = hgt
                    series_dict['data'] = data
                    s = str(series_dict)

                    # this is an ugly hack which could potentially lead to errors if " u'" occurs at the end of a string
                    s =  s.replace(" u'", " '")

                    
                    # change single quotes to double
                    s = s.replace("'", '"')
                    
                    # replace masked values. Again, ugly
                    s = s.replace('masked', 'null')
                    
                    series.append(s)
    

                    #fout.write(s)
                    #end of height loop, write comma but not last time in loop
                    #if h<len(hgts)-1:
                    #    fout.write(',\n')
                #if v<nvars-1:
                #    fout.write(',\n')
            
            #fout.write(']')
            #fout.close()
        
        
        
        #fout.write(']')
        #fout.close()

        dataset.close()        

        fname = '%s/fcst_data.json' % (out_dir)
        logger.debug('********* writing json to %s ****************'  % fname)

        fout  = open(fname, 'w')
        json_data = ',\n'.join(series)
        fout.write('[')
        fout.write(json_data)
        fout.write(']')
        fout.close()
        check_json(fname)
        
        
def check_json(fname):
    try:
        '\n\n Checking %s ' % fname
        json.loads(fname)
        print "Valid JSON"
    
    except ValueError, err:
        print "Invalid JSON"
        msg = err.message
        print msg

   
    
if __name__ == '__main__':
    main()

