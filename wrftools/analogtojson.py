""" analogtojson.py creates json series power output from wind speed and direction times series 

Usage:
    analogtojson.py [--config=<file>] [options]
       
        
Options:
        --config=<file>           file specifiying configuration options
        --log_name=<name>         name of logger, allows shared loggers between modules
        --log_level=<level>       log level, debug, info or warn
        --log_file=<file>         write log output to file as well as stdout
        --log_fmt=<fmt>           formart of log messages, see logging module for details
        --init_time=<datetime>    initial time of forecast
        --operational=<bool>      if true, calculate initial time from closest cycle to current time
        --cycles=<cycles>         list of cycle hours to consider, e.g. 00,06,12,18
        --delay=<hours>           if operational=true, subtract hours from now
        --analog_in_dir=<dir>     location of analog text files
        --analog_out_dir=<dir>    location of output json files"""


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
LOGGER="analogstojson"

def main():
    config = conf.config(__doc__, sys.argv[1:], flatten=True)
    analogtojson(config)

def strptime(str):
    return datetime.datetime(*time.strptime(str, '%Y-%m-%d_%H:%M:%S')[0:5])
    
    
def analogtojson(config):
    """Reads output from analog text files and writes JSON """

    #logger       = log.create(config['log_name'], config['log_level'], config['log_fmt'], config['log_file'])
    logger   = log.create_logger(config)
    
    out_dir  = config['analog_out_dir']
    out_name = 'analogs.json' 
    
    
    if config['operational']:
        now = datetime.datetime.today()
        if config['delay']:
            delay = int(config['delay'])
            hour = datetime.timedelta(0, 60*60)        
            now = now - delay * hour
        
        cycles = config['cycles']
        init_time = get_operational_init_time(now, cycles)
        logger.debug(init_time)
        
    else:
        init_time = config['init_time']
        
    input_file = '%s/UTH_%s' % (config['analog_in_dir'], init_time.strftime('%Y-%m-%d_%H'))
    logger.debug(input_file)
    if not os.path.exists(input_file):
        raise Exception("File not found %s" % input_file)

    frame = pd.read_csv(input_file, parse_dates=['init', 'valid'])
    
    frame.columns = ['init', 'valid', 'POWER.An', 'SPEED.An', 'POWER.An.P10', 'POWER.An.P30', 'POWER.An.P50', 'POWER.An.P75', 'POWER.An.P90', 'SPEED.NWP']
    
    logger.debug(frame)
    
    logger.debug(frame['valid'].to_string())
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
        d['location'] = 'UTH'
        d['variable'] = name
        d['GRID_ID'] = 1
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
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    fout = open('%s/%s' % (out_dir, out_name), 'w')
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