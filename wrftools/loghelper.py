import logging

def create(name, log_level, log_fmt, log_file=None):

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
    

def get(name):
    return logging.getLogger(name)
