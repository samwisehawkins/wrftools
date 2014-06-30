import os
import glob
import shared

__all__ = ['produce_ncl_plots', 'produce_ncl_ol_plots']


def _fix_ncarg_env():
    os.environ['NCARG_NCARG'] = '%s/lib/ncarg' % os.environ['NCARG_ROOT']



def produce_ncl_plots(config):
    """ Calls a series of ncl scripts to produce visualisations.
    
    Need to think about how to define a flexible visualisation framework
    Currently communication with NCL is via environment variables
    Perhaps in future we should move to PyNGL for easier (direct) integration
    as then we could simply pass in the config dictionary, use the same logging 
    framework, and make use of a vtable like mapping to forecast vars.
    
    However, for the time being we design each ncl script to expect 
    certain environment variables.  Then, the list of ncl scripts to 
    run can simply be specified somewhere in the config file
    e.g. wrf_basic_plots.ncl, wrf_vertical_plots.ncl etc.
    
    Updated: Some plots are much easier to produce using the original 
    wrfout netcdf files, rather than use the UPP post-processed grib files. 
    Howeverm in future we should stick with one or the other.
    
    
    Arguments:
    config -- dictionary containing various configuration options """
    
    logger = shared.get_logger()    

     

    domain         = config['domain']
    model_run      = config['model_run']
    working_dir    = config['working_dir']
    ncl_code_dir   = config['ncl_code_dir']
    ncl_files      = config['ncl_code']
    #ncl_code      = ['%s/%s' % (ncl_code_dir, f) for f in ncl_files]
    ncl_code       =  ncl_files
    ncl_log        = config['ncl_log']
    wrfout_dir     = config['wrfout_dir']
    init_time      = config['init_time']
    dom            = config['dom']
    fcst_file      = '%s/wrfout_d%02d_%s:00:00.nc' %(wrfout_dir, dom, init_time.strftime("%Y-%m-%d_%H"))
    ncl_in_file    = fcst_file
    ncl_loc_file   = config['locations_file']
    ncl_out_dir    = shared.sub_date(config['ncl_out_dir'], init_time=init_time)
    ncl_out_type   = config['ncl_out_type']
    nest_id        =  '%02d' % dom

    logger.info('*** RUNNING NCL SCRIPTS FOR DOMAIN d%02d***' % dom)
    
    if not os.path.exists(ncl_out_dir):
        os.makedirs(ncl_out_dir)

    #
    # Communicate to NCL via environment variables
    # NCL expects the following to be set
    #File    = getenv("FCST_FILE")
    #type    = getenv("NCL_OUT_TYPE")
    #diro    = getenv("NCL_OUT_DIR")
    #;web_dir = getenv("WEB_DIR")
    #domain  = getenv("NEST_ID")    
    #run_hour = getenv("RUN_HOUR")

    #
    # Try escaping : in fcst_file
    #
    #fcst_file = fcst_file.replace(':', r'\:')
    #os.environ['FCST_FILE']      = fcst_file
    #os.environ['LOCATIONS_FILE'] = loc_file
    #os.environ['NCL_OUT_DIR']    = ncl_out_dir
    #os.environ['NCL_OUT_TYPE']   = ncl_out_type
    #os.environ['NEST_ID']        = nest_id
    #os.environ['DOMAIN']         = domain
    #os.environ['MODEL_RUN']      = model_run

    logger.debug('ncl_in_file  ----> %s' % ncl_in_file)
    logger.debug('ncl_out_dir  ----> %s' % ncl_out_dir)
    logger.debug('ncl_out_type ----> %s' % ncl_out_type)
    logger.debug('ncl_loc_file ----> %s' % ncl_loc_file)

    if not ncl_in_file.endswith('.nc'):
        ncl_in_file = ncl_in_file + '.nc' 
    
    
    for script in ncl_code:
        #
        # mem_total forces the use postprocessing node
        #
        #cmd  = "ncl %s >> %s 2>&1" % (script, ncl_log)
        #qcmd = 'qrsh -cwd -l mem_total=36G "%s"' % cmd
        logger.debug(script)
        
        queue = config['queue']
        if queue['ncl']:
            cmd  = """ncl ncl_in_file="%s" ncl_out_dir="%s" ncl_out_type="%s" ncl_loc_file="%s" %s""" % (ncl_in_file,ncl_out_dir, ncl_out_type, ncl_loc_file, script)
        else:
            cmd  = """ncl 'ncl_in_file="%s"' 'ncl_out_dir="%s"' 'ncl_out_type="%s"' 'ncl_loc_file="%s"' %s 2>&1 >> %s/ncl.log""" % (ncl_in_file,ncl_out_dir, ncl_out_type, ncl_loc_file, script, working_dir)
        
        ret = shared.run(cmd, config)


def produce_ncl_ol_plots(config):
    """ Calls a series of ncl scripts to produce visualisations.
    
    Need to think about how to define a flexible visualisation framework
    Currently communication with NCL is via environment variables
    Perhaps in future we should move to PyNGL for easier (direct) integration
    as then we could simply pass in the config dictionary, use the same logging 
    framework, and make use of a vtable like mapping to forecast vars.
    
    However, for the time being we design each ncl script to expect 
    certain environment variables.  Then, the list of ncl scripts to 
    run can simply be specified somewhere in the config file
    e.g. wrf_basic_plots.ncl, wrf_vertical_plots.ncl etc.
    
    Updated: Some plots are much easier to produce using the original 
    wrfout netcdf files, rather than use the UPP post-processed grib files. 
    Howeverm in future we should stick with one or the other.
    
    
    Arguments:
    config -- dictionary containing various configuration options """
    
    logger = shared.get_logger()    
    logger.info('*** RUNNING NCL SCRIPTS ***')
     
    working_dir  = config['working_dir']

    ncl_code_dir   = config['ncl_code_dir']
    ncl_files      = config['ncl_ol_code']
    #ncl_code       = ['%s/%s' % (ncl_code_dir, f) for f in ncl_files]
    ncl_code       = ncl_files
    ncl_log        = config['ncl_log']
    wrftools_dir   = config['wrftools_dir']
    wrfout_dir     = config['wrfout_dir']
    init_time      = config['init_time']
    dom            = config['dom']
    fcst_file      = '%s/wrfout_d%02d_%s:00:00.nc' %(wrfout_dir, dom, init_time.strftime("%Y-%m-%d_%H"))
    ncl_out_dir    = shared.sub_date(config['ncl_ol_out_dir'], init_time=init_time)
    ncl_out_type   = config['ncl_out_type']
    nest_id        =  '%02d' % dom
    

    ncl_in_file    = fcst_file
    ncl_loc_file   = config['locations_file']
    ncl_out_dir    = shared.sub_date(config['ncl_out_dir'], init_time=init_time)
    ncl_out_type   = config['ncl_out_type']


    if not os.path.exists(ncl_out_dir):
        os.makedirs(ncl_out_dir)

    #
    # Communicate to NCL via environment variables
    # NCL expects the following to be set
    #File    = getenv("FCST_FILE")
    #type    = getenv("NCL_OUT_TYPE")
    #diro    = getenv("NCL_OUT_DIR")
    #;web_dir = getenv("WEB_DIR")
    #domain  = getenv("NEST_ID")    
    #run_hour = getenv("RUN_HOUR")

    #
    # Try escaping : in fcst_file
    #
    #fcst_file = fcst_file.replace(':', r'\:')
    #os.environ['FCST_FILE']      = fcst_file
    #os.environ['NCL_OUT_DIR']    = ncl_out_dir
    #os.environ['NCL_OUT_TYPE']   = ncl_out_type
    #os.environ['NEST_ID']        = nest_id
    #os.environ['DOMAIN']         = domain
    #os.environ['MODEL_RUN']      = model_run



    #logger.debug('Setting environment variables')
    logger.debug('FCST_FILE    ----> %s' % fcst_file)
    logger.debug('NCL_OUT_DIR  ----> %s' % ncl_out_dir)
    logger.debug('NCL_OUT_TYPE ----> %s' % ncl_out_type)
    logger.debug('NEST_ID      ----> %s' % nest_id)
    logger.debug('PATH')
    logger.debug(os.environ['PATH'])
    #logger.debug('DOMAIN       ----> %s' % domain)
    #logger.debug('MODEL_RUN    ----> %s' % model_run)


    for script in ncl_code:
        #cmd  = "ncl %s >> %s 2>&1" % (script, ncl_log)
        cmd  = "ncl %s " % script
        #qcmd = 'qrsh -cwd -l mem_total=36G "%s"' % cmd
        
        logger.warn("NCL to produce GEOTIFFS does not work on post-processing queue, runnign on head node")

        

        cmd  = """ncl 'ncl_in_file="%s"' 'ncl_out_dir="%s"' 'ncl_out_type="%s"' 'ncl_loc_file="%s"' %s 2>&1 >> %s/ncl.log""" % (ncl_in_file,ncl_out_dir, ncl_out_type, ncl_loc_file, script, working_dir)

        ret = shared.run_cmd(cmd, config)
        
        
        gwarp = config['gwarp']
        os.chdir(ncl_out_dir)
        
        cmd = "%s %s/*.tiff" %(gwarp, ncl_out_dir)
        logger.debug(cmd)
        shared.run_cmd(cmd, config)

        
        
def transfer_to_web_dir(config):
    """ Transfers all plots in output folder to web folder"""
    
    logger = shared.get_logger()    
    logger.debug('Transferring plot files to web dir')
    init_time      = config['init_time']    
    full_trace     = config['full_trace']
    ncl_out_dir    = shared.sub_date(config['ncl_out_dir'], init_time=init_time)
    ncl_web_dir    = shared.sub_date(config['ncl_web_dir'], init_time=init_time)
    
    if not os.path.exists(ncl_web_dir):
        os.makedirs(ncl_web_dir)
    
    flist = glob.glob(ncl_out_dir+'/*')
    shared.transfer(flist, ncl_web_dir, mode='copy', debug_level='NONE')

    ncl_out_dir    = shared.sub_date(config['ncl_ol_out_dir'], init_time=init_time)
    ncl_web_dir    = shared.sub_date(config['ncl_ol_web_dir'], init_time=init_time)
    
    if not os.path.exists(ncl_web_dir):
        os.makedirs(ncl_web_dir)
    
    flist = glob.glob(ncl_out_dir+'/*')
    shared.transfer(flist, ncl_web_dir, mode='copy', debug_level='NONE')


    
