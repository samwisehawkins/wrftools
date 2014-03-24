import os
import re
import json 
import logging 
import pandas as pd


class ConfigError(Exception):
    pass


def load_config(config):
    
    if not os.path.exists(config):
        raise Exception("configuration file not found")
    return json.load(open(config))
   
   
def merge(dict_1, dict_2):
    """Merge two dictionaries.    
    Values that evaluate to true take priority over falsy values.    
    `dict_1` takes priority over `dict_2`.    """    
    
    return dict((str(key), dict_1.get(key) or dict_2.get(key))
            for key in set(dict_2) | set(dict_1))

def expand_cmd_args(args):
    """Parse command line arguments which look like lists as json.
    
    Arguments: 
        args -- a dictionary mapping argument names to their values
        
    Returns:
        a new dictionary with any list-like values expanded"""
    
    jargs = {}
    lexp = re.compile("\[.*\]")
    for (k,v) in args.items():
        if v and type(v)==type("") and lexp.match(v):
            jv = json.loads(v)
            jargs[k] = jv
        else:
            jargs[k] = v
    return jargs

            
def create_logger(name, log_level, log_fmt, log_file=None):
    """ Creates a logging instance. If log_file is specified, handler is a
    FileHandler, otherwise StreamHandler"""
    
    logger = logging.getLogger(name)    
    numeric_level = getattr(logging, log_level.upper(), None)
    logger.setLevel(numeric_level)
    formatter = logging.Formatter(log_fmt)    
    
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(numeric_level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    
    if log_file:
        log_handler = logging.FileHandler(log_file,mode='w')
        log_handler.setLevel(numeric_level)
        log_handler.setFormatter(formatter)
        logger.addHandler(log_handler)

    return logger

def load_input(fname, delim, missing, parse_dates):

    if type(fname)!=type([]):
        result = pd.read_csv(fname, sep=delim, parse_dates=parse_dates)
    
    if type(fname)==type([]):
        frames = []
        for f in fname:
            frames.append(pd.read_csv(f, sep=delim, parse_dates=parse_dates))
        result = pd.concat(frames)
    
    return result
    
    
def save(frame, fname, float_format=None):

    if not os.path.exists(fname):
        frame.to_csv(fname, index=False, float_format=float_format)
        return
        
    response = raw_input('%s exists, overwrite with generated data? ' % fname)
    if response.lower().strip()=='y':
        frame.to_csv(fname, index=False, float_format=float_format)
    