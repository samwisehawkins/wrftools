"""dispatch.py sends files via email using mutt. 

Re-written to make this a standalone application, as wrftools is getting too bloated.
Relies takes a json file as configuration options, and goes through a list of directories sending emails
Question is how to run, since we will need to substitute some times into the the file names based on the inital_time

Usage: dispatch.py [--config=<file>] [options]
            

Options: --config=<file>         json/yaml configuration file specifiying options
         --init_time=<datetime>  initial time which will get subsituted into file names
         --dispatch.list=<dict>  json/yaml file specifying files to distributed
         --dry_run               if present, just log but don't send mail
         --log_level=<level>     logging level, info, debug or warn
         --log_file=<file>       log file to write to
         --log_format=<fmt>      log message format (see logging module docs)"""

import sys
import os
import json
import subprocess
import loghelper
import confighelper as conf
import docopt
import datetime
import time
from substitute import expand
LOGGER = "dispatch"

    
def main():
    config = conf.config(__doc__, sys.argv[1:], flatten=True, format="yaml")
    dispatch(config)


def dispatch(config):

    if __name__ == "__main__":
        logger = loghelper.create_logger(config)
    else:
        logger = loghelper.get_logger(config['log.name'])

    dist = config['dispatch.list']
    logger.info("dispatch.py sending files via email")
    dry_run=config['dry_run']
    
    for name, entry in dist.items():
        logger.info("dispatching files for entry: %s" % name)
        dispatch_entry(config, entry, dry_run=dry_run, log_name=config['log.name'])
        
        
        
def dispatch_entry(config, entry, dry_run=None, log_name=LOGGER):    
    """Dispacthes one entry of distribution list"""
    
    logger          = loghelper.get_logger(log_name)
    
    address   = expand(entry['mailto'], config)
    subject   = expand(entry['subject'], config)
    body      = expand(entry['body'], config)
    from_addr = expand(entry['from'], config)
    attachments = [expand(a, config) for a in entry['attach']]

    logger.debug('dispatch_entry() called')
    
    if type(attachments)==type([]):
        a_arg = ' '.join(['-a %s' % a for a in attachments])
    else:
        a_arg = '-a %s' % attachments 
    
    if 'cc' in  entry:
        cc_arg = '-c %s' % entry['cc']
    else:
        cc_arg = ''

    if 'content_type' in entry:
        ct_arg = '-e "my_hdr Content-Type: :%s"' % dist['content_type']
    else:
        ct_arg = ''

        
    cmd = """EMAIL="%s" mutt %s -s"%s" %s %s -- %s < %s """ %(from_addr, ct_arg, subject, a_arg, cc_arg, address, body)
    logger.debug(cmd)
    logger.debug(dry_run)
    if not dry_run:
        subprocess.call(cmd, shell=True)

if __name__ == '__main__':
    main()
