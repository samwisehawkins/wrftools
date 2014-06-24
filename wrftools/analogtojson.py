""" analogtojson.py creates json series power output from wind speed and direction times series 

Usage:
    analogtojson.py <input>...
       
        
Options:
        <input>       filename(s) of input file to process  """


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
import docopt

LOGGER="analogstojson"

def main():
    config = docopt.docopt(__doc__, sys.argv[1:])
    analogtojson(config)

def strptime(str):
    return datetime.datetime(*time.strptime(str, '%Y-%m-%d_%H:%M:%S')[0:5])
    
def strftime(dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S')

def analogtojson(config):
    """Reads output from analog text files and writes JSON """

    
    input_files = config['<input>']
    
    series = []
        
    for n,input_file in enumerate(input_files):
      
        if not os.path.exists(input_file):
            raise IOError("File not found %s" % input_file)

        path, name = os.path.split(input_file)
        location = name[0:3]
        #init_time = strptime(name[4:]+":00:00")

        frame = pd.read_csv(input_file, parse_dates=['init', 'valid'], date_parser=strptime)
        frame.columns = ['init', 'valid', 'POWER.An', 'SPEED.An', 'POWER.An.P10', 'POWER.An.P30', 'POWER.An.P50', 'POWER.An.P70', 'POWER.An.P90', 'SPEED.NWP']

        # Bit of a hack to ease output formatting, convert init_time to string
        #frame['init'] = frame['init'].apply(str)
        frame['init'] = frame['init'].apply(strftime)
        init_time = frame.init[0]        
        # we need to group by everything except valid time and value
        #group_by = [c for c in frame.columns if c not in ["valid_time", "value"]]
        #gb = frame.groupby(group_by)

            
        # Convert time to milliseconds since epoc
        convert = lambda t: time.mktime(t.timetuple())*1000        
        
            
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


            # create a dictionary from all the fields except valid time and value
            
            timestamp = map(convert, frame['valid'])
            values  = frame[name]
            mvals   = np.ma.masked_invalid(np.array(values))
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
    
    
    #fout = open(output_file, 'w')
    print('['),
    #fout.write('[')
    print(json_str),
    print(']')
    #fout.close()

    
    
    
    
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