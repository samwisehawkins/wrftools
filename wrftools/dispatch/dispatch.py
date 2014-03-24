"""dispatch.py sends files via email using mutt. 

Re-written to make this a standalone application, as wrftools is getting too bloated.
Relies takes a json file as configuration options, and goes through a list of directories sending emails
Question is how to run, since we will need to substitute some times into the the file names based on the inital_time

Usage: dispatch.py <distribution> <init_time> [--config=<file>]
            [--date-fmt=<fmt>]
            [--dry-run]
            [--log-level=<level>]
            [--log-file=<file>]
            [--log-format=<fmt>]

Options: <init_time>             initial time which will get subsituted into file names
         <distribution>          json file specifying files to distributed
         --config=<file>         configuration file with further options [default: defaults.json]
         [--dry-run]             if present, just log but don't send mail
         [--date-fmt]            date format to parse init_time
         [--log-level=<level>]   logging level, info, debug or warn
         [--log-file=<file>]     log file to write to
         [--log-format=<fmt>]    log message format (see logging module docs)"""

import sys
import os
import json
import subprocess
import logging
import scripting as sc
import docopt
import datetime
import time

LOGGER = "dispatch"

    
def main():
    
    args  = docopt.docopt(__doc__, sys.argv[1:])

    # since command-line args are not parsed as json unlike the config file,
    # any lists come back as single strings, e.g. "[arg1, arg2]"
    # this ensures they are parsed as json, and become lists
    args = sc.expand_cmd_args(args)

    # load config file or defaults
    cfile = sc.load_config(args['--config'])
    
    # merge, with command-line args taking precendence
    # note, if an argument is not specified in either source, its value will be None
    config = sc.merge(args, cfile)

    # create a logging instance
    logger = sc.create_logger(LOGGER, config['--log-level'], config['--log-format'])

    logger.debug(json.dumps(config, indent=4))
    
    # parse init_time
    init_time = datetime.datetime(*time.strptime(config['<init_time>'], config['--date-fmt'])[0:5])

    # load distribution list, this will be a nested dictionary
    # should we expand the strings now, or as we send out?
    # do we put the loop here, or inside te function
    #distribution = json.load(open(config['<distribution>'], 'r'))

    #
    # Expansion is actually easier on the raw string, as we don't
    # have to recurse into nested dictionaries
    #
    dispatch_all(config['<distribution>'], init_time, config['--dry-run'])

def dispatch_all(distribution, init_time, dry_run, log_name):

    logger = logging.getLogger(log_name)
    fname = _sub_date(distribution, init_time=init_time)
    f = open(fname, 'r')
    s = f.read()
    
    distribution =  json.loads(s)
    f.close()
    logger.info("dispatch.py sending files via email")
        
    for name, dist in distribution.items():
        logger.info("dispatching files for entry: %s" % name)
        _expand_dates(dist, init_time)
        dispatch(dist, dry_run)
        
        
        
def dispatch(dist, dry_run=None):    
    """Dispacthes one entry of distribution list"""
    
    logger          = logging.getLogger(LOGGER)
    logger.debug(json.dumps(dist, indent=4))
    
    address   = dist['mailto']
    subject   = dist['subject']
    body      = dist['body']
    from_addr = dist['from']
    attachments = dist['attachments']

    
    if type(attachments)==type([]):
        a_arg = ' '.join(['-a %s' % a for a in attachments])
    else:
        a_arg = '-a %s' % attachments 
    
    if 'cc' in dist:
        cc_arg = '-c %s' % dist['cc']
    else:
        cc_arg = ''

    if 'content_type' in dist:
        ct_arg = '-e "my_hdr Content-Type: :%s"' % dist['content_type']
    else:
        ct_arg = ''

        
    cmd = """EMAIL="%s" mutt %s -s"%s" %s %s -- %s < %s """ %(from_addr, ct_arg, subject, a_arg, cc_arg, address, body)
    logger.debug(cmd)
    if not dry_run:
        pass
        #subprocess.call(cmd, shell=True)

def _expand_dates(dic, init_time):
    logger = logging.getLogger()
    for key,value in dic.items():
        if "%" in value:
            new_value =  _sub_date(value, init_time=init_time)
            logger.debug("expanded %s ---> %s" % (value, new_value))
            dic[key] = new_value

    
def _sub_date(s, init_time=None, valid_time=None):
    """Substitues a date into a string following standard format codes.
    Syntax of original string s:
    i  -- initial time
    v  -- valid time
    %y -- 2-digit year
    %Y -- 4-digit year
    %m -- 2 digit month
    %d -- 2-digit day
    %H -- 2 digit hour
    %M -- 2-digit minute
    %S -- 2-digit second 
    
    Returns: string with codes expanded"""
    
    if init_time:
    
        yi  = str(init_time.year)[2:]
        Yi  = str(init_time.year)
        mi  = '%02d' % init_time.month
        di  = '%02d' % init_time.day
        Hi  = '%02d' % init_time.hour
        Mi  = '%02d' % init_time.minute
        Si  = '%02d' % init_time.second

        #s = s.replace('%iY', Yi).replace('%iy',yi).replace('%im',mi).replace('%id', di).replace('%iH', Hi).replace('%iM', Mi).replace('%iS', Si)

        s = s.replace('%iY', Yi)
        s = s.replace('%iy', yi)
        s = s.replace('%im', mi)
        s = s.replace('%id', di) 
        s = s.replace('%iH', Hi)
        s = s.replace('%iM', Mi)
        s = s.replace('%iS', Si)

    if valid_time:
        yv  = str(init_time.year)[2:]
        Yv  = str(init_time.year)
        mv  = '%02d' % valid_time.month
        dv  = '%02d' % valid_time.day
        Hv  = '%02d' % valid_time.hour
        Mv  = '%02d' % valid_time.minute
        Sv  = '%02d' % valid_time.second
        
        s = s.replace('%vY', Yv)
        s = s.replace('%vy',yv)
        s = s.replace('%vm',mv)
        s = s.replace('%vd', dv) 
        s = s.replace('%vH', Hv)
        s = s.replace('%vM', Mv)
        s = s.replace('%vS', Sv)

    if init_time and valid_time:
        delta = valid_time - init_time
        fhr   = delta.days * 24 + int(delta.seconds / (60*60))
        fH    = '%02d' % fhr
        s = s.replace('%fH', fH)
    
    return s

if __name__ == '__main__':
    main()
