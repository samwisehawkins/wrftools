import os
import glob
import shared

    
def finalise(config):
    """Removes files, transfers etc."""

    logger = shared.get_logger()

    logger.info('*** FINALISING ***')
    
    working_dir    = config['working_dir']
    
    
    links       = [shared.expand(x, config) for x in config['finalise.link']]
    remove      = [shared.expand(x, config) for x in config['finalise.remove']]
    subdirs     = [shared.expand(x, config) for x in config['finalise.create']]
    copy        = [shared.expand(x, config) for x in config['finalise.copy']]
    move        = [shared.expand(x, config) for x in config['finalise.move']]
    run         = [shared.expand(x, config) for x in config['finalise.run']]
    
        
    fulldirs  = subdirs 
    for d in fulldirs:
        if not os.path.exists(d):
            logger.debug('creating directory %s ' %d)
            os.mkdir(d) 
   
    
    for arg in move:
        cmd = "mv %s" % arg
        shared.run_cmd(cmd, config)

    for arg in copy:
        cmd = "cp %s" % arg
        shared.run_cmd(cmd, config)        
        
    for pattern in links:
        shared.link(pattern)
    
    for cmd in run:
        shared.run_cmd(cmd, config)
    
    for pattern in remove:
        flist = glob.glob(pattern)
        for f in flist:
            if os.path.exists(f):
                os.remove(f)
    
    logger.info('*** DONE FINALISE ***')    