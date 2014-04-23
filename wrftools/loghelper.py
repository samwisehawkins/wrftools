import logging

def create_logger(config):
    

    logger = create(config['log_name'],config['log_level'], config['log_fmt'],config.get('log_file'), config.get('log_mail'), config.get('mailto'), config.get('mail_subject'), config.get('mail_level'),config.get('mail_buffer'))
    return logger

def get_logger(name):
    return logging.getLogger(name)


def create(name, log_level, log_fmt, log_file=None, log_mail=None, mailto=None, subject=None, mail_level=None, buffer=None):

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

    if log_mail:
        from customloggers import BufferingSendmailHandler

        mail_level = getattr(logging, mail_level.upper(), None)
        eh = BufferingSendmailHandler(mailto, subject, buffer)
    
        eh.setLevel(mail_level)
        eh.setFormatter(formatter)
        logger.addHandler(eh)
    
    logger.debug('logging object created')
    return logger

        
        
def get(name):
    return logging.getLogger(name)
        