import logging

def create_logger(config):
    

    logger = create(config['log.name'],config['log.level'], config['log.fmt'],config.get('log.file'), config.get('log.mail'), config.get('log.mail.to'), config.get('log.mail.subject'), config.get('log.mail.level'),config.get('log.mail.buffer'))
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
        
        if mail_level:
            level=mail_level.upper()
        else:
            level='INFO'
        
        mail_level = getattr(logging, level, None)
        eh = BufferingSendmailHandler(mailto, subject, buffer)
    
        eh.setLevel(mail_level)
        eh.setFormatter(formatter)
        logger.addHandler(eh)
    
    logger.debug('logging object created')
    return logger

        
        
def get(name):
    return logging.getLogger(name)
        
        
def shutdown():
    logging.shutdown()