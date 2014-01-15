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
import scipy.stats as stats
import string

COORD_VARS      = ['time', 'height', 'location', 'lat', 'lon', 'location_id']
FILE_DATE_FMT   = '%Y-%m-%d_%H%M'  # Date format for file name
DATE_FMT        = '%Y-%m-%d %H:%M' # Date format within files
GLOBAL_ATTS     = ['DOMAIN', 'MODEL_RUN', 'GRID_ID']  # which global attributes to copy from ncfile to json
GLOBAL_ATTS     = ['GRID_ID']  # which global attributes to copy from ncfile to json
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

    if 'txt' in args['--format']:
        write_seperate_files(ncfiles, out_dir, dims)
    
    if 'json' in args['--format']:
        write_json_files(ncfiles, GLOBAL_ATTS, VAR_ATTS,COORD_VARS,out_dir, FILE_DATE_FMT, dimspec)
    
    if 'csv' in args['--format']:
        write_csv_files(ncfiles, out_dir, dimspec)
    
    if 'aot' in args['--format']:
        write_aot_files(ncfiles, out_dir, dimspec=dimspec)
    
    else:
        print 'format not understood'



def frame_from_nc(ncfiles, dimspec=FULL_SLICE):
    """ Build a Pandas DataFrame from a series of netcdf files
    
    Arguments:
        @ncfiles -- a list of netcdf files to read
        @dimspec -- dictionary specifying start and end indices of coordinated dimensions"""

        
    ts,te = dimspec['time']
    ls,le = dimspec['location']
    hs,he = dimspec['height']

    rows = []
    for f in ncfiles:
        dataset = Dataset(f, 'r')
        # get some global attributes

        grid_id       = dataset.GRID_ID
        variables     = dataset.variables

        fulltime      = variables['time']
        fulldatetimes = num2date(fulltime,units=fulltime.units,calendar=fulltime.calendar)
        
        time      = fulltime[ts:te]
        datetimes = fulldatetimes[ts:te]
        ntime     = len(datetimes) 
        init_time = fulldatetimes[0]
      
        # hack to catch thanet
        try:
            location    = variables['location'][ls:le]
        except KeyError:
            location    = variables['location_id'][ls:le] 
        
        nloc        = location.shape[0]
        loc_id_raw  = [''.join(location[l,0:-1]) for l in range(nloc)]
        loc_id      = map(string.strip, loc_id_raw)
        height    = variables['height'][hs:he]
        nheight   = len(height)

        # this will force the reading all of the required variable data into memory
        varnames = [v for v in variables if v not in COORD_VARS]
        vardata  = dict([(v, variables[v][:]) for v in varnames])

        for t in range(ntime):
            for l in range(nloc):
                rowdict = OrderedDict()
                rowdict['valid_time']  = datetimes[t]
                rowdict['location']    = loc_id[l]
                rowdict['init_time']   = init_time
                rowdict['grid_id']     = grid_id
                
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
    
    #re-arrange columns
    cols = df.columns
    pre_cols = ['init_time','valid_time','location']
    data_cols = [c for c in cols if c not in pre_cols]
    new_cols = pre_cols + data_cols
    df = df[new_cols]
    return df

    
def write_aot_files(ncfiles, out_dir, dimspec=FULL_SLICE):        
    """Writes file format the same as AOTs existing supplier, which is:
  
    
    "Location","Date/time (utc)","Date/time (local)","Forecast (hours)","Windspeed 21m (m/sec)","Winddirection 21m (degrees)","Windspeed 70m (m/sec)","Winddirection 70m (degrees)","Windspeed 110m (m/sec)","Winddirection 110m (degrees)","Percentile  10 (m/sec) 70m","Percentile  20 (m/sec) 70m","Percentile  30 (m/sec) 70m","Percentile  40 (m/sec) 70m","Percentile  50 (m/sec) 70m","Percentile  60 (m/sec) 70m","Percentile  70 (m/sec) 70m","Percentile  80 (m/sec) 70m","Percentile  90 (m/sec) 70m
    "Thanet",2013-05-31 00:00,2013-05-31 02:00,0,7.80,351,8.70,352,8.93,352,7.27,7.83,8.20,8.52,8.70,8.97,9.27,9.66,10.16
    
    Arguments:
        @ncfiles netcdf time-series files to process
        @out_dir directory to write output to
        @locations additional table giving information about the locations"""
    
    logger = wrftools.get_logger()
    
    df = frame_from_nc(ncfiles, dimspec)

    #
    # The AOT files require a local time, as well as UTC time. This requires a mapping between location 
    # and timezone. The quickest way to do this is to hardcode this here. This is not very elegant or
    # extensible, but it works.
    #
    import pytz
    tz_map = { "FRE": "Europe/Amsterdam",
                    "HAM":	"Europe/Amsterdam",
                    "DTK":	"Europe/Amsterdam",
                    "SNB":	"Europe/Amsterdam",
                    "AVS":	"Europe/Amsterdam",
                    "FN1":	"Europe/Amsterdam",
                    "FN3":	"Europe/Amsterdam",
                    "AMS":	"Europe/Amsterdam",
                    "NEZ":	"Europe/Amsterdam",
                    "ZDB":	"Europe/Amsterdam",
                    "RCN":	"Europe/Amsterdam",
                    "BEK":	"Europe/Amsterdam",
                    "DEB":	"Europe/Amsterdam",
                    "DKY":	"Europe/Amsterdam",
                    "DLN":	"Europe/Amsterdam",
                    "HGV":	"Europe/Amsterdam",
                    "LWN":	"Europe/Amsterdam",
                    "LYD":	"Europe/Amsterdam",
                    "SPL":	"Europe/Amsterdam",
                    "SVN":	"Europe/Amsterdam",
                    "VLK":	"Europe/Amsterdam",
                    "ZSN":	"Europe/Amsterdam",
                    "STO":	"Europe/Amsterdam",
                    "SLG":	"Europe/Amsterdam",
                    "YTS":	"Europe/Amsterdam",
                    "UTG":	"Europe/Amsterdam",
                    "EA1":	"Europe/London",
                    "EAZ":	"Europe/London",
                    "EDI":	"Europe/London",
                    "LON":	"Europe/London",
                    "UKF":	"Europe/London",
                    "UTH":	"Europe/London",
                    "UKR":	"Europe/London",
                    "EDB":	"Europe/London"}

    name_map = {"FRE" : "Fredericia",
                "EDI" : "Edinburgh",
                "LON" : "London",
                "STO" : "Stockholm",
                "HAM" : "Hamburg",
                "AMS" : "Amsterdam",
                "UKF" : "Kentish Flats",
                "UTH" : "Thanet",
                "UKR" : "Ormonde",
                "SLG" : "Lillgrund",
                "DTK" : "Dan Tysk",
                "SNB" : "Sand Bank",
                "EDB" : "Edinbane",
                "NEZ" : "Egmonde an Zee",
                "ZDB" : "Zuidlob",
                "AVS" : "Alpha Ventus",
                "RCN" : "RCN Mast",
                "FN1" : "Fino 1 Platform",
                "FN3" : "Fino 3 Platform",
                "BEK" : "Beek",
                "DEB" : "Debilt",
                "DKY" : "Dekooy",
                "DLN" : "Deelen",
                "HGV" : "Hoogeveen",
                "LWN" : "Leeuwarden",
                "LYD" : "Lelystad",
                "SPL" : "Schipol",
                "SVN" : "Stavoren",
                "VLK" : "Valkenburg",
                "ZSN" : "Zestienhoven",
                "EA1" : "East Anglia 1B",
                "EAZ" : "East Anglia ZE",
                "YTS" : "Yttre Stengrund",
                "UTG" : "Utgrunded"}

    #
    # We also need to rename (and drop) some columns which we will hard code here
    #
    col_map = OrderedDict([("location",   "Location"),
                               ("valid_time",    "Date/time (utc)"),
                               ("local_time",    "Date/time (local)"),
                               ("lead_time",     "Forecast (hours)"),
                               ("SPEED_020",     "Windspeed 21m (m/sec)"),
                               ("DIRECTION_020", "Winddirection 21m (degrees)"),
                               ("SPEED_070",     "Windspeed 70m (m/sec))"),
                               ("DIRECTION_070", "Winddirection 70m (degrees)"),
                               ("SPEED_110",     "Windspeed 110m (m/sec)"),
                               ("DIRECTION_110", "Winddirection 110m (degrees)"),
                               ("SPEED_070.P10", "Percentile  10 (m/sec) 70m"),
                               ("SPEED_070.P20", "Percentile  20 (m/sec) 70m"),
                               ("SPEED_070.P30", "Percentile  30 (m/sec) 70m"),
                               ("SPEED_070.P40", "Percentile  40 (m/sec) 70m"),
                               ("SPEED_070.P50", "Percentile  50 (m/sec) 70m"),
                               ("SPEED_070.P60", "Percentile  60 (m/sec) 70m"),
                               ("SPEED_070.P70", "Percentile  70 (m/sec) 70m"),
                               ("SPEED_070.P80", "Percentile  80 (m/sec) 70m"),
                               ("SPEED_070.P90", "Percentile  90 (m/sec) 70m") ])


    utc = pytz.UTC
    # weeeeee, what a lot of chained operators!
    convert = lambda row: utc.localize(row['valid_time']).astimezone(pytz.timezone(tz_map[row['location']])).strftime('%Y-%m-%d %H:%M')
    
    
    # Now we apply our uber-lambda function to insert local time
    df['local_time'] = df.apply(convert, axis=1)

    # Calculate lead time as integer number of hours
    deltas = df['valid_time'] - df['init_time']
    hours = lambda x: x / np.timedelta64(1, 'h')
    lead_ints = deltas.apply(hours)
    df['lead_time'] = lead_ints.astype(int)

    # Expand short names to long names
    rename = lambda x: name_map[x]
    long_names = df['location'].apply(rename)
    df['location'] = long_names
    
    
    # *******************************************
    # WARING - this is a hack and does not belong
    # here long term. This is just a quick way of
    # adding statistical percentiles to the output 
    # time series. We need to thinl carefully about
    # where these shoudl be calculated.
    #********************************************
#     "SPEED_070.P10" : "Percentile  10 (m/sec) 70m",
#                  "SPEED_070.P20" : "Percentile  20 (m/sec) 70m",
#                  "SPEED_070.P30" : "Percentile  30 (m/sec) 70m",
#                  "SPEED_070.P40" : "Percentile  40 (m/sec) 70m",
#                  "SPEED_070.P50" : "Percentile  50 (m/sec) 70m",
#                  "SPEED_070.P60" : "Percentile  60 (m/sec) 70m",
#                  "SPEED_070.P70" : "Percentile  70 (m/sec) 70m",
#                  "SPEED_070.P80" : "Percentile  80 (m/sec) 70m",
#                  "SPEED_070.P90" : "Percentile  90 (m/sec) 70m" 
    
    percentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90]
    for p in percentiles:
        pname = 'SPEED_070.P%02d' % p
        pfunc = lambda x : stats.norm.ppf(p/100.0, x, x*0.10)
        df[pname] = df['SPEED_070'].apply(pfunc)

    print df[['SPEED_070', 'SPEED_070.P20', 'SPEED_070.P90']].to_string()
    
    subset = df[col_map.keys()]
    subset.columns = col_map.values()

    gb = subset.groupby(by='Location')
    groups = dict(list(gb))
    import csv
    for location in groups.keys():
        group = groups[location]
        out_name = '%s/%s.csv' % (out_dir, location)
        group.to_csv(out_name, index=False, float_format='%0.2f')
    

        
        
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
    df = frame_from_nc(ncfiles, dimspec)
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

        # Output file name
        fname = '%s/fcst_data_d%02d_%sZ.json' % (out_dir, nest_id, init_time.strftime('%H'))


        
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

        #fname = '%s/fcst_data.json' % (out_dir)
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
        json.load(open(fname))
        print "Valid JSON"
    
    except ValueError, err:
        print "Invalid JSON"
        msg = err.message
        print msg

   
    
if __name__ == '__main__':
    main()

