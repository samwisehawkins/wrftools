""" analogtojson.py creates json series power output from wind speed and direction times series 

Usage:
    analogtojson.py [--config=<file>] [options]
       
        
Options:
        --config=<file>           file specifiying configuration options
        --config-fmt=<str>        config file format, json or yaml
        --log_name=<name>         name of logger, allows shared loggers between modules
        --log_level=<level>       log level, debug, info or warn
        --log_file=<file>         write log output to file as well as stdout
        --log_fmt=<fmt>           formart of log messages, see logging module for details
        --init_time=<datetime>    initial time of forecast
        --operational=<bool>      if true, calculate initial time from closest cycle to current time
        --cycles=<cycles>         list of cycle hours to consider, e.g. 00,06,12,18
        --delay=<hours>           if operational=true, subtract hours from now
        --analog_in_dir=<dir>     location of analog text files
        --analog_out_dir=<dir>    location of output json files
        --file_in=<pattern>       filename of input file to process  
        --file_out=<pattern>      filename of output file
        --num_files=<int>         number of files to process -1=most recent, not present=all"""


import os
import sys
import confighelper as conf
import loghelper as log
import pandas as pd
import numpy as np
import dateutil
import json
import datetime
import time
import substitute
import glob


LOGGER="analogstojson"

def main():
    config = conf.config(__doc__, sys.argv[1:], flatten=True)
    analogtojson(config)

def strptime(str):
    return datetime.datetime(*time.strptime(str, '%Y-%m-%d_%H:%M:%S')[0:5])
    
    
def analogtojson(config):
    """Reads output from analog text files and writes JSON """

    #
    # Rules: if init_time specified, work out filename from that
    #        else use last file in sorted list with prefix
    #
    logger   = log.create_logger(config)
    
    if config['init_time']:
        input_files  = [substitute.sub_date(config['file_in'], config['init_time'])]
        output_files = [substitute.sub_date(config['file_out'], config['init_time'])]
    

    else:
        # append a wildcard to pattern

        pattern = config['file_in'] + '*'
        logger.debug(pattern)
        all_files = sorted(glob.glob(pattern))
        
        if not config['num_files']:
            input_files = all_files
        
        # if number of files has been specified
        else:
            num_files = config['num_files']
            
            # if negative number, count backwards through list
            if num_files<0:
                input_files = all_files[-1:num_files-1:-1]
            else:
                input_files = all_files[0:num_files]

            if len(input_files)==0:
                raise IOError("no input files found")
      
        
    for n,input_file in enumerate(input_files):
    
       
        if not os.path.exists(input_file):
            raise IOError("File not found %s" % input_file)

        path, name = os.path.split(input_file)
        location = name[0:3]
        #init_time = strptime(name[4:]+":00:00")
        output_file = input_file.replace(config['file_in'], config['file_out'])+".json"
        logger.debug(input_file)
        logger.debug(output_file)

        frame = pd.read_csv(input_file, parse_dates=['init', 'valid'])
        
        frame.columns = ['init', 'valid', 'POWER.An', 'SPEED.An', 'POWER.An.P10', 'POWER.An.P30', 'POWER.An.P50', 'POWER.An.P70', 'POWER.An.P90', 'SPEED.NWP']
        init_time = frame.init[0]
     
        # Bit of a hack to ease output formatting, convert init_time to string
        #frame['init'] = frame['init'].apply(str)
        frame['init'] = frame['init'].apply(str)
        frame['valid'] = frame['valid'].apply(strptime)
        
        # we need to group by everything except valid time and value
        #group_by = [c for c in frame.columns if c not in ["valid_time", "value"]]
        #gb = frame.groupby(group_by)

            
        # Convert time to milliseconds since epoc
        convert = lambda t: time.mktime(t.timetuple())*1000        
        
        series = []
        
        for name in frame.columns:

            if name=='init' or name=='valid':
                continue
            
            d = {}
            d['location']  = location
            d['variable']  = name
            d['GRID_ID']   = 1
            d['init_time'] = str(init_time)
            d['height']    = 80
            d['model_run'] = 'analogs'

            logger.debug("processing %s" % str(name))
            # create a dictionary from all the fields except valid time and value

            
            timestamp = map(convert, frame['valid'])
            values  = frame[name]
            mvals = np.ma.masked_invalid(np.array(values))
            data    = [ (timestamp[n],mvals[n]) for n in range(len(timestamp))]
            ldata   = map(list, data)
            d['data'] = ldata
            s = str(d)
        
            # this is an ugly hack which could potentially lead to errors if " u'" occurs at the end of a string
            s =  s.replace(" u'", " '")
                    
            # change single quotes to double
            s = s.replace("'", '"')
            
            # replace masked values. Again, ugly
            s = s.replace('masked', 'null')
            
            series.append(s)

        json_str = ','.join(series)
        
        
        fout = open(output_file, 'w')
        fout.write('[')
        fout.write(json_str)
        fout.write(']')
        fout.close()

    
    
    
    
def get_operational_init_time(now,cycles):
    """ Returns a list of most recent init times for an operational forecast"""
    

    hour = datetime.timedelta(0, 60*60)                
    delayed_time  = now
    
    start_day     = datetime.datetime(delayed_time.year, delayed_time.month, delayed_time.day, 0, 0)           # throw away all time parts
    start_hour    = delayed_time.hour
    past_cycles   = [ c for c in cycles if (c <= start_hour)]
    recent_cycle  = past_cycles[-1]
    start         = start_day + recent_cycle * hour

    return start    


if __name__ == "__main__":
    main()