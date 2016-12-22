""" Script for downloading all boundary condition files need for WRF runs 

Config comes from a file, specified as --config argument. Some configuration options (listed below) 
can also be given at the command line, where they will override the configuration file. 
See example/forecast.yaml for a full list of configuration options. 

Usage:
    fetch.py --config=<file> [--log-level=<level>] [--log-file=<file>] [--log-fmt=<fmt>] <times>
    
Options:
    --config=<file>         yaml configuration file
    --log-level=<level>     log level info, debug or warn (see python logging modules)
    --log-format=<fmt>      log format code (see python logging module)
    --log-file=<file>       optional log file
    <times>                 either single time, or file with times, one per line"""

LOGGER="wrftools"

import sys
import os
import subprocess
import confighelper as conf
import loghelper
import requests
from urlparse import urlparse
from wrftools import substitute
from wrftools import shared

        
def main():


    # merge command-line and file-specified arguments
    config = conf.config(__doc__, sys.argv[1:])

    logger = loghelper.create(LOGGER, log_level=config.get('log.level'), 
                              log_fmt=config.get('log.format'), 
                              log_file=config.get('log.file'))
    
    init_times = shared.read_times(config['<times>'])
    
    for init_time in init_times:
        fetch(config, init_time)

    
def fetch(config, init_time):
    
    logger = loghelper.get(LOGGER)

    for key,entry in config['fetch'].items():
        # apply any delay and rounding to the init_time to get correct time for dataset
        # note that sometimes it is necessary to use a different time e.g. for SST field is delayed by one day

        base_time = shared.get_time(init_time, delay=entry.get('delay'), round=entry.get('cycles'))
        length = int(entry['length'])
        interval = int(entry['interval'])
        
        bdy_times = shared.get_bdy_times(base_time, length, interval)

        remote_patterns = entry['remote_files']
        local_pattern = entry['local_files']
        
        # each remote pattern specifies an alternate source to try
        for remote_pattern in remote_patterns:
            # create an ordered set to ensure filenames only appear once
            remote_filenames = shared.ordered_set([substitute.sub_date(remote_pattern, init_time=base_time, valid_time=t) for t in bdy_times])
            local_filenames = shared.ordered_set([substitute.sub_date(local_pattern, init_time=base_time, valid_time=t) for t in bdy_times])
            assert(len(remote_filenames)==len(local_filenames))
            
            first_file = remote_filenames[0]
            if 'http' in first_file:
                success = fetch_http(remote_filenames, local_filenames)
            elif 'ftp' in first_file:
                success = fetch_ftp(remote_filenames, local_filenames)
            
            # don't try any more remote files, we got them all
            if success:
                break
    

def fetch_ftp(remotes, locals):
    
    assert(len(remotes)==len(locals))
    
    # use the first file to get server and path details
    remote = remotes[0]
    local =  locals[0]

    parts =  urlparse(remote)
    server = parts.netloc
    remote_dir, remote_name = os.path.split(parts.path)
    local_dir, local_name = os.path.split(local)
    
    remote_paths = [urlparse(f).path for f in remotes]
    remote_names = [os.path.split(p)[1] for p in remote_paths]
    
    # first we will save the files with original names, then potentially move them
    interim_files = [ '%s/%s' % (local_dir, f) for f in remote_names] 
    
    
    proxy = os.environ['http_proxy']
    script = '/tmp/lftpscript'
    lftpscript = open(script, 'w')
    lftpscript.write('lcd %s\n' % local_dir)    
    lftpscript.write('set ftp:proxy %s\n' % proxy) 
    lftpscript.write('set hftp:use-type no\n')
    lftpscript.write('open %s\n' % server)
    for f in remote_names:
        lftpscript.write('get %s/%s\n' % (remote_dir,f))
    lftpscript.write('bye')
    lftpscript.close()
    
    
    cmd = '/usr/bin/lftp -f %s' % script
    subprocess.call(cmd, shell=True)
    
    
    failed_files = [f for f in interim_files if not os.path.exists(f)]
    if failed_files!=[]:
        raise IOError('files: %s not downloaded' % str(str(failed_files)))

    for interim, final in zip(interim_files, locals):
        if interim!=final:
            os.rename(interim, final)
        
    os.remove(script)
    return True

    
def fetch_http(remotes, locals):
    
    assert(len(remotes)==len(locals))

    for remote,local in zip(remotes, locals):
        print('fetching %s --> %s ...' % (remote, local),)
        
        if os.path.exists(local):
            print('...already exists, skipping')
            continue
        r = requests.get(remote, stream=True)
        print(r.status_code)
        if r.status_code == 200:
            
            with open(local, 'wb') as f:
                for chunk in r:
                    f.write(chunk)    
            print('  ok')
            success = True
        
        else:
            success = False
    return success
        
if '__main__' in __name__:
    main()
