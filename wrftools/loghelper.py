import logging
import inspect

DEFAULT_LEVEL = "INFO"
DEFAULT_FMT = "%(message)s"



def create(name, log_level=None, log_fmt=None, log_file=None):

    """ Creates a logging instance. If log_file is specified, handler is a
    FileHandler, otherwise StreamHandler"""
    
    level = log_level if log_level else DEFAULT_LEVEL
    fmt = log_fmt if log_fmt else DEFAULT_FMT
    
    logger = logging.getLogger(name)    
    numeric_level = getattr(logging, level.upper(), None)
    logger.setLevel(numeric_level)
    formatter = logging.Formatter(fmt)    
    
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
    
def file_handler(log_file, level, fmt):
    numeric_level = getattr(logging, level.upper(), None)
    formatter = logging.Formatter(fmt)    

    log_handler = logging.FileHandler(log_file,mode='w')
    log_handler.setLevel(numeric_level)
    log_handler.setFormatter(formatter)
    return log_handler




def get(name):
    return logging.getLogger(name)

def get2():
    return logging.getLogger(inspect.stack()[-1][1])