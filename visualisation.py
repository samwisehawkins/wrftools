import os
import wrftools
import io


__all__ = ['produce_ncl_plots', 'run_jesper_script', 'transfer_to_web_dir']


def _fix_ncarg_env():
    os.environ['NCARG_NCARG'] = '%s/lib/ncarg' % os.environ['NCARG_ROOT']


def run_jesper_script(config):
    """Temporary measure for producing visualisations from jesper's
    csh script. Eventually this can be replaced by produce NCL plots """


    logger = wrftools.get_logger()
    logger.info("running jesper's ncl script")
    init_time = config['init_time']
    init_str = init_time.strftime('%Y%m%d%H')
    _fix_ncarg_env()
    run_hour = init_time.hour
    logger.debug('setting environment variable run_hour to %02d' % init_time.hour)
    os.environ['run_hour'] = '%02d' % run_hour
    cmd = "/home/jepn/work/web_forecast/MakePlots4.csh %s" % init_str
    wrftools.run_cmd(cmd, config)
  


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
    
    logger = wrftools.get_logger()    
    logger.info('*** RUNNING NCL SCRIPTS ***')
     
    domain_dir     = config['domain_dir']
    domain         = config['domain']
    model_run      = config['model_run']
    ncl_code_dir   = config['ncl_code_dir']
    ncl_files      = config['ncl_code']
    ncl_code       = ['%s/%s' % (ncl_code_dir, f) for f in ncl_files]
    ncl_log        = config['ncl_log']

    wrfout_dir     = '%s/%s/wrfout'%(domain_dir, model_run)
    init_time      = config['init_time']
    dom            = config['dom']
    fcst_file      = '%s/%s/wrfout/wrfout_d%02d_%s:00:00.nc' %(domain_dir, model_run, dom, init_time.strftime("%Y-%m-%d_%H"))
    loc_file       = config['locations_file']
    ncl_out_dir    = wrftools.sub_date(config['ncl_out_dir'], init_time)
    ncl_out_type   = config['ncl_out_type']
    nest_id        =  '%02d' % dom

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
    os.environ['FCST_FILE']      = fcst_file
    os.environ['LOCATIONS_FILE'] = loc_file
    os.environ['NCL_OUT_DIR']    = ncl_out_dir
    os.environ['NCL_OUT_TYPE']   = ncl_out_type
    os.environ['NEST_ID']        = nest_id
    os.environ['DOMAIN']         = domain
    os.environ['MODEL_RUN']      = model_run



    logger.debug('Setting environment variables')
    logger.debug('FCST_FILE    ----> %s' % fcst_file)
    logger.debug('NCL_OUT_DIR  ----> %s' % ncl_out_dir)
    logger.debug('NCL_OUT_TYPE ----> %s' % ncl_out_type)
    logger.debug('NEST_ID      ----> %s' % nest_id)
    logger.debug('DOMAIN       ----> %s' % domain)
    logger.debug('MODEL_RUN    ----> %s' % model_run)


    for script in ncl_code:
        #
        # mem_total forces the use postprocessing node
        #
        cmd  = "ncl %s >> %s" % (script, ncl_log)
        qcmd = 'qrsh -cwd -l mem_total=36G "%s"' % cmd
        ret = wrftools.run_cmd(cmd, config)

        
        
def transfer_to_web_dir(config):
    """ Transfers all plots in output folder to web folder"""
    
    logger = wrftools.get_logger()    
    logger.debug('Transferring plot files to web dir')
    init_time      = config['init_time']    
    ncl_out_dir    = wrftools.sub_date(config['ncl_out_dir'], init_time)
    web_out_dir    = wrftools.sub_date(config['web_dir'], init_time)
    if not os.path.exists(web_out_dir):
        os.makedirs(web_out_dir)
    
    cmd            = "cp -f %s/* %s" % (ncl_out_dir,  web_out_dir)
    ret            = wrftools.run_cmd(cmd, config)
    if ret!=0:
        raise IOError("Error while copying plot files")
        
    #cmd = "rm -f %s/*" % (ncl_out_dir)
    #wrftools.run_cmd(cmd, config)
