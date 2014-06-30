import shared
import os
import glob

def prepare(config):
    """Removes files specified in pre_clean. Creates subdirectories specfied in create_dirs,
    links files specified in wrf_links into wrf_working_dir."""

   
    working_dir    = config['working_dir']
    
    links          = config['prepare.link']
    pre_clean      = config['prepare.remove'] 
    subdirs        = config['prepare.create']

    logger         = shared.get_logger()
    logger.info('*** PREPARING ***')

    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
    
    #fulldirs = [ working_dir+'/'+d for d in subdirs ]
    fulldirs  = subdirs 
    for d in fulldirs:
        if not os.path.exists(d):
            logger.debug('creating directory %s ' %d)
            os.mkdir(d) 
   
    for pattern in pre_clean:
        flist = glob.glob(pattern)
        for f in flist:
            if os.path.exists(f):
                logger.debug('removing file: %s' % f )
                os.remove(f)


    for pattern in links:
        shared.link(pattern)
    logger.info('*** DONE PREPARE ***')