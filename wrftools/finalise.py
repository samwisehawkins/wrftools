import shared

def run_scripts(config):
    """Simply runs whatever scripts are specified in the config file. 
    Sets a few environment variables first """
    logger = get_logger()
    
    
    domain_dir     = config['domain_dir']
    domain         = config['domain']
    model_run      = config['model_run']
    init_time      = config['init_time']
    nest_id        = config['dom']
    loc_file       = config['locations_file']
    scripts        = config['run_scripts']
    
    fcst_file      = '%s/%s/wrfout/wrfout_d%02d_%s:00:00.nc' %(domain_dir, model_run, nest_id, init_time.strftime("%Y-%m-%d_%H"))

    os.environ['FCST_FILE']      = fcst_file
    os.environ['LOCATIONS_FILE'] = loc_file
    os.environ['NEST_ID']        = str(nest_id)
    logger.info('*** RUNNING ADDITIONAL SCRIPTS ***')
    logger.warn('Checking success of external scripts is not yet implemented')
    for s in scripts:
        run_cmd(s, config)
    
    logger.info('*** FINISHED ADDITIONAL SCRIPTS ***')


def cleanup(config):
    """Cleans up various files """
    logger = get_logger()

    logger.debug('**** CLEANUP FILES ****')
    init_time   = config['init_time']
    post_clean  = config['post_clean']
    cleanup_dir = [sub_date(s, init_time=init_time) for s in post_clean]
    
    for d in cleanup_dir:
        cmd = 'rm -f %s' % d
        logger.debug(cmd)
        run_cmd(cmd, config)

    logger.info('*** FINISHED CLEANUP ***')
