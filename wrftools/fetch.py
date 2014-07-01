import os
import datetime
import subprocess
import shared


def run_gribmaster(config):
    """Runs the gribmaster programme to download the most recent boundary conditions """
    logger      = shared.get_logger()
    gm_dir      = config['gm_dir']
    gm_transfer = config['gm_transfer']
    gm_dataset  = config['gm_dataset']
    start       = config['init_time']
    fcst_hours  = config['fcst_hours']
    gm_log      = config['gm_log']
    gm_sleep    = config['gm_sleep'] # this is in minutes
    gm_max_attempts = int(config['gm_max_attempts'])

    log_dir = '/home/slha/forecasting'
       
    cmd     = '%s/gribmaster --verbose --%s --dset %s --date %s --cycle %s --length %s > %s' %(gm_dir, gm_transfer, gm_dataset, start.strftime('%Y%m%d'), start.strftime('%H'), fcst_hours, gm_log )

    for attempt in range(gm_max_attempts):
        logger.info('*** RUNNING GRIBMASTER, %s attempt ***' % (attempt+1))
        shared.run_cmd(cmd, config)
        
        cmd = 'grep "BUMMER" %s' % gm_log # check for failure
        ret = subprocess.call(cmd, shell=True)
        # if we positively find the string BUMMER, we know we have failed
        if ret==0:
            logger.error('*** FAIL GRIBMASTER: Attempt %d of %d ***' % (attempt+1, gm_max_attempts))
            logger.info('Sleeping for %s minutes' % gm_sleep) 
            time.sleep(gm_sleep*60)
        
        # else we check for definite sucess
        else:
            cmd = 'grep "ENJOY" %s' % gm_log # check for failure
            ret = subprocess.call(cmd, shell=True)
            if ret==0:
                logger.info('*** SUCESS GRIBMASTER ***')
                return
        
        
    raise IOError('gribmaster did not find files after %d attempts' % gm_max_attempts)
    
    

def get_sst(config):
    """ Downloads SST fields from an ftp server.
    Whoever is running this must have the http_proxy environment variable set
    correctly to allow them to download files through the proxy.  Example:
    http_proxy = http://slha:password@webproxy-se.corp.vattenfall.com:8080"""
    logger      = shared.get_logger()
    # create an lftpscript in model run dir
    
    logger.info('*** FETCHING SST ***')
    working_dir    = config['working_dir']
    tmp_dir        = config['tmp_dir']
    http_proxy     = os.environ['http_proxy']
    home           = os.environ['HOME']
    sst_server     = config['sst_server']
    sst_server_dir = config['sst_server_dir']
    sst_local_dir  = config['sst_local_dir']
    sst_time       = shared.get_sst_time(config)
    sst_filename   = shared.sub_date(shared.get_sst_filename(config), init_time=config['init_time'])
   
    if not os.path.exists(sst_local_dir):
        os.makedirs(sst_local_dir)
    
    if os.path.exists('%s/%s' %(sst_local_dir, sst_filename)):
        logger.info('*** SST ALREADY EXISTS LOCALLY, NOT DOWNLOADED ***')
        return
    
    lftpfilename = '%s/lftpscript' % working_dir
    logger.debug('Writing lftpscript to %s' % lftpfilename)
    lftpscript     = open(lftpfilename, 'w')    
    lftpscript.write('lcd %s\n' % sst_local_dir)    
    lftpscript.write('set ftp:proxy %s\n' % http_proxy) 
    lftpscript.write('set hftp:use-type no\n')
    lftpscript.write('open %s\n' % sst_server)
    lftpscript.write('get %s/%s\n' % (sst_server_dir,sst_filename))
    lftpscript.write('bye')
    lftpscript.close()
    
    cmd = '/usr/bin/lftp -f %s' % lftpfilename
    shared.run_cmd(cmd, config)
    # check if file downloaded

    if not os.path.exists('%s/%s' %(sst_local_dir, sst_filename)):
        raise IOError('SST file: %s not downloaded' % sst_filename)
    logger.info('*** SUCCESS SST DOWNLOADED ***')