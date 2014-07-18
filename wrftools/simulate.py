import os
import shutil
import subprocess
from collections import OrderedDict
import datetime
import re
import glob
import shared



def link_namelist_wps(config):
    """Links namelist_wps into wps_run_dir"""    
    
    logger = shared.get_logger()
    #
    # link namelist.wps file from domain dir to 
    # wps dir. Fist check it exists
    #
    namelist_wps = config['namelist_wps']
    namelist_run = '%s/namelist.wps' % config['wps_run_dir']
    
    #
    # Check if namelist exists in working_dir directory
    #    
    if not os.path.exists(namelist_wps):
        raise IOError('could not find namelist.wps file: %s' % namelist_wps)
        
    if os.path.exists(namelist_run):
        logger.debug('removing existing namelist.wps file: %s' % namelist_run)
        os.remove(namelist_run)
    
    #
    # Execute this command even in a dummy run, so that namelist file is linked
    # correctly and can be updated by other commands
    #
    cmd = 'ln -sf %s %s ' %(namelist_wps, namelist_run)
    logger.debug(cmd)
    subprocess.call(cmd, shell=True)
        
    

    
def prepare_wps(config):
    """ Runs all the pre-processing steps necessary for running WPS.
    
    Reads the current value of init_time from config, and links 
    boundary condition files into correct directory. Creates an output
    directory for the met_em files.
    
    Arguments:
    config -- dictionary containing various configuration options"""
    
    logger       = shared.get_logger()
    logger.debug('*** PREPARING FILES FOR WPS ***')
    
    wps_dir       = config['wps_dir']          # the base installation of WPS
    wps_run_dir   = config['wps_run_dir']      # the directory to run WPS from
    working_dir = config['working_dir']    # model run directory 
    met_em_dir    = config['met_em_dir']
    init_time     = config['init_time']

    
    grb_input_fmt = config['grb_input_fmt']
    vtable        = config['vtable']
    bdy_times     = shared.get_bdy_times(config)

    if type(grb_input_fmt)==type({}):
        logger.debug(grb_input_fmt)
        fmts = grb_input_fmt.values()
        
    else:
        fmts = [grb_input_fmt]
    
    
    for fmt in fmts:
        #
        # Generate filelist based on the initial time, and the forecast hour
        #        
        filelist = shared.get_bdy_filenames(fmt, bdy_times)

        #
        # Check the boundary files exist
        #
        logger.debug('checking boundary condition files exists')    
        for f in filelist:
            if not os.path.exists(f):
                raise IOError('cannot find file: %s' %f)
        
    logger.debug('all boundary conditions files exist')
    
    #
    # Run the link_grib scipt to link the FNL files
    #
    logger.debug('running link_grib.csh script to link grib files to GRIBFILE.AAA etc')
    os.chdir(wps_run_dir)
    args = ' '.join(filelist)
    cmd = '%s/link_grib.csh %s' %(wps_run_dir,args)
    shared.run_cmd(cmd, config)

    logger.debug('Path for met_em files is %s' % met_em_dir)
    if not os.path.exists(met_em_dir):
        os.makedirs(met_em_dir)

   
    logger.debug('*** FINISHED PREPARING FILES FOR WPS ***')    



def update_namelist_wps(config):
    """ Updates the namelist.wps to reflect updated settings in config
    
    Arguments:
    config -- dictionary containing various configuration options
        
    """    
    logger     = shared.get_logger()
    logger.debug('*** UPDATING namelist.wps ***')

    #domain_dir = config['domain_dir']
    #model_run  = config['model_run']
    #wps_dir    = config['wps_dir']
    wps_run_dir= config['wps_run_dir']          # required for opt_geogrid_tbl_path
    #bdy_conditions = config['bdy_conditions'] 
    
    namelist_wps = config['namelist_wps']
    shutil.copyfile(namelist_wps, namelist_wps+'.backup')
    
    bdy_times  = shared.get_bdy_times(config)
    
    max_dom    = config['max_dom']
    init_time  = config['init_time']

    met_em_dir = shared.sub_date(config['met_em_dir'], init_time=init_time)
    geo_em_dir = config['geo_em_dir']

    bdy_interval = config['bdy_interval']
    interval_seconds = bdy_interval * 60 * 60

    logger.debug('reading namelist.wps <--------- %s' % namelist_wps)
    namelist = shared.read_namelist(namelist_wps)

    #
    # Update some options based on the forecast config file
    #
    namelist.update('max_dom', max_dom)
    namelist.update('opt_output_from_geogrid_path', geo_em_dir, section='share')
    namelist.update('opt_geogrid_tbl_path', wps_run_dir, section='geogrid')
    namelist.update('opt_metgrid_tbl_path', wps_run_dir, section='metgrid')
    namelist.update('interval_seconds', [interval_seconds])
    
    #
    # Generate formatted strings for inclusion in the namelist.wps file
    #
    start_str  = bdy_times[0].strftime("%Y-%m-%d_%H:%M:%S")
    end_str    = bdy_times[-1].strftime("%Y-%m-%d_%H:%M:%S")
    logger.debug("Updating namelist.wps start and end")
    logger.debug(start_str)
    logger.debug(end_str)

    namelist.update('start_date', [start_str]*max_dom)
    namelist.update('end_date',   [end_str]*max_dom)

        
    logger.debug('writing modified namelist.wps to file')
    namelist.to_file(namelist_wps)
    logger.debug('*** FINISHED UPDATING namelist.wps ***')


def ungrib_sst(config):
    """ Runs ungrib.exe for SST fields, makes and modifies a copy of namelist.wps,
    then restores the original namelist.wps"""
    logger = shared.get_logger()
    
    wps_dir      = config['wps_dir']
    wps_run_dir  = config['wps_run_dir']
    tmp_dir      = config['tmp_dir']
    working_dir  = config['working_dir']
    init_time    = config['init_time']
    max_dom      = config['max_dom']
    sst_local_dir = config['sst_local_dir']
    sst_time     = shared.get_sst_time(config)
    sst_filename = shared.get_sst_filename(config)
    vtable_sst   = wps_dir+'/ungrib/Variable_Tables/'+config['sst_vtable']
    #vtable_dom   = wps_dir+'/ungrib/Variable_Tables/'+config['vtable']
    vtable       = wps_run_dir+'/Vtable'
    queue        = config['queue']
    log_file     = '%s/ungrib.sst.log' % wps_run_dir
    namelist_wps  = config['namelist_wps']
    namelist_sst  = '%s/namelist.sst' % working_dir

    namelist      = shared.read_namelist(namelist_wps)

    #
    # update one line to point to the new SST field
    # ungrib.exe will name SST field as e.g.
    # SST:2013-04-24_00
    #
    constants_name = '%s/SST:%s' %(wps_run_dir, sst_time.strftime('%Y-%m-%d_%H'))
    logger.debug('Updating constants_name ----> %s' % constants_name)
    namelist.update('constants_name', constants_name, section='metgrid')

    # Write the changes into the original
    namelist.to_file(namelist_wps)

    #
    # Update start and end time to process SST
    #
    start_str  = sst_time.strftime("%Y-%m-%d_%H:%M:%S")
    end_str    = sst_time.strftime("%Y-%m-%d_%H:%M:%S")
    logger.debug("Updating namelist.sst")
    logger.debug('PREFIX ------> SST')
    logger.debug('start_date---> ' +start_str)
    logger.debug('end_date-----> '+ end_str)

    namelist.update('prefix', 'SST')
    namelist.update('start_date', [start_str]*max_dom)
    namelist.update('end_date',   [end_str]*max_dom)
    logger.debug('writing modified namelist.sst to file -------> %s' % namelist_sst)
    namelist.to_file(namelist_sst)

    #remove any linked namelist.wps 
    logger.debug('removing namelist.wps')
    namelist_run = '%s/namelist.wps' % wps_run_dir
    if os.path.exists(namelist_run):
        os.remove(namelist_run)

    # link namelist.sst to namelist.wps in WPS run dir
    logger.debug('linking namelist.sst -----> namelist.wps')
    cmd = 'ln -sf %s %s' %(namelist_sst, namelist_run)
    shared.run_cmd(cmd, config)

    logger.debug('removing Vtable')
    if os.path.exists(vtable):
        os.remove(vtable)
    logger.debug('linking Vtable.SST ----> Vtable')
    cmd = 'ln -sf %s %s' %(vtable_sst, vtable)
    shared.run_cmd(cmd, config)

    # run link_grib to link SST gribs files
    logger.debug('Linking SST GRIB files')
    cmd = '%s/link_grib.csh %s/%s' %(wps_dir, sst_local_dir, sst_filename)
    shared.run_cmd(cmd, config)


    logger.info('*** RUNNING UNGRIB FOR SST ***')
    cmd     =  '%s/ungrib.exe' % wps_run_dir
    shared.run(cmd, config, wps_run_dir)

    cmd = 'grep "Successful completion" ./ungrib.log*' # check for success
    ret = shared.run_cmd(cmd, config)
    if ret!=0:
        raise IOError('Ungrib failed for SST')
    
    logger.info('*** SUCCESS UNGRIB SST ***')
    logger.debug('Removing namelist.wps')
    if os.path.exists(namelist_run): 
        os.remove(namelist_run)
    # link in original (unmodified) namelist.wps
    cmd = 'ln -sf %s %s' %(namelist_wps, namelist_run)    
    shared.run_cmd(cmd, config)
    
def prepare_ndown(config):
    """Runs a one-way nested simulation using ndown.exe
    We assume the coarse resolution run has been done, 
    and we have wrfout_d01.date files.
    
    We only need to run metgrid for the initial forecast time.
    
    We have two options, either we force the user to do all the renaming themselves, 
    or we allow them to utilise the original namelist.input file, and add effectivley
    add a column onto that. This could be done via a bunch of smaller utility steps.
    e.g. shift_namelist namelist.input 3 > namelist.input
    
    Which would rotate the columns of a namelist.input file so that the n-th column 
    becomes the first column.
    
        
    Therefore we have to run ungrib, geogrid, metgrid
    Assume the geo_em files exist for both domains.
    What """

    logger =shared.get_logger()
    logger.info('*** PREPARING NDOWN ***')
    namelist_wps   = config['namelist_wps']
    namelist_input = config['namelist_input']
    max_dom        = config['max_dom']
    wrf_run_dir    = config['wrf_run_dir']
    
    
    if max_dom!=2:
        raise ConfigError("max_dom must equal 2 when doing ndown runs")
    
    bdy_times = shared.get_bdy_times(config)
    ndown_fmt = config['ndown_fmt']
    
    wrfout_d01_files = [shared.sub_date(ndown_fmt, init_time=bdy_times[0], valid_time=t) for t in bdy_times]
    for f in wrfout_d01_files:
        if not os.path.exists(f):
            raise MissingFile("File: %s missing" % f)
        cmd = 'ln -sf %s %s' % (f, wrf_run_dir)
        shared.run_cmd(cmd, config)
    
    
    # Check for wrfinput_d02
    wrfinput_d02 = '%s/wrfinput_d02' % wrf_run_dir
    if not os.path.exists(wrfinput_d02):
        raise MissingFile("wrfinput_d02 is missing")
    
    os.rename('%s/wrfinput_d02' % wrf_run_dir, '%s/wrfndi_d02' % wrf_run_dir)
    
    
    namelist         = read_namelist(namelist_input)
    
    # History interval is in minutes
    history_interval = namelist.settings['history_interval']
    interval_seconds = history_interval[0] * 60
    namelist.update('interval_seconds', interval_seconds)
    namelist.insert('io_form_auxinput2', 2, 'time_control')
    namelist.to_file(namelist_input)
    
    logger.info('*** DONE PREPARE NDOWN ***')
    
def run_ndown(config):
    logger =shared.get_logger()
    logger.info('*** RUNNING NDOWN ***')
    
    wrf_run_dir = config['wrf_run_dir']
    queue       = config['queue']
    log_file    = '%s/ndown.log' % wrf_run_dir
    
    cmd = '%s/ndown.exe' % wrf_run_dir
    
    nprocs = config['num_procs']
    poll_interval = config['poll_interval']
    logger.debug(poll_interval)
    logger.debug(nprocs)
    logger.debug(nprocs['ndown.exe'])
    
    shared.run(cmd, config, wrf_run_dir)
        
    cmd = 'grep "Successful completion" %s' % log_file # check for success
    ret =shared.run_cmd(cmd,config)
    if ret!=0:
        raise IOError('ndown.exe did not complete')
    
    logger.info('*** SUCESS NDOWN ***')

    
    
    
    
def run_ungrib(config):
    """ Runs ungrib.exe and checks output was sucessfull
    If vtable and gbr_input_fmt are NOT dictionaries, 
    then dictionarius will be constructed from them using 
    the key bdy_conditions from the metadata
    
    Arguments:
    config -- dictionary specifying configuration options
    
    """
    logger        =shared.get_logger()
    wps_dir       = config['wps_dir']
    wps_run_dir   = config['wps_run_dir']
    namelist_wps  = config['namelist_wps']
    working_dir   = config['working_dir']    
    met_em_dir    = config['met_em_dir']
    init_time     = config['init_time']
    log_file      = '%s/ungrib.log' % wps_run_dir
    vtable        = config['vtable']
    grb_input_fmt  = config['grb_input_fmt']
    grb_input_delay = config.get("grb_input_delay")  # this allows None to be returned 
    
    bdy_conditions = config['bdy_conditions']
    
    
    
    
    
    logger.info("*** RUNNING UNGRIB ***")
    
    namelist = shared.read_namelist(namelist_wps)
    
    bdy_times     = shared.get_bdy_times(config)
    

    if type(grb_input_fmt)!=type({}):
        grb_input_fmt = {bdy_conditions:grb_input_fmt}

    if type(vtable)!=type({}):
        vtable = {bdy_conditions:vtable}


    #
    # Check that boundary conditions exist
    #     
    for key in vtable.keys():
        
        
        if grb_input_delay and key in grb_input_delay:
            logger.debug("applying delay")
            delay = datetime.timedelta(0, grb_input_delay[key]*60*60)
            new_bdy_times = [b - delay for b in bdy_times]
        else:
            logger.debug("no delay applied")
            new_bdy_times = bdy_times
        
        fmt = grb_input_fmt[key]
        #
        # Generate filelist based on the initial time, and the forecast hour
        #        
        filelist = list(OrderedDict.fromkeys(shared.get_bdy_filenames(fmt, new_bdy_times)))

        #
        # Check the boundary files exist
        #
        logger.debug('checking boundary condition files exists')    
        for f in filelist:
            if not os.path.exists(f):
                raise IOError('cannot find file: %s' %f)
        
    
    
    logger.debug('all boundary conditions files exist')
    
    #
    # Now process boundary conditions
    #
    for key in vtable.keys():

        if grb_input_delay and key in grb_input_delay:
            logger.debug("applying delay")
            delay = datetime.timedelta(0, grb_input_delay[key]*60*60)
            new_bdy_times = [b - delay for b in bdy_times]
        else:
            logger.debug("no delay applied")
            new_bdy_times = bdy_times
        
        fmt = grb_input_fmt[key]
        #
        # Generate filelist based on the initial time, and the forecast hour
        #        
        filelist = list(OrderedDict.fromkeys(shared.get_bdy_filenames(fmt, new_bdy_times)))

        
        logger.debug('running link_grib.csh script to link grib files to GRIBFILE.AAA etc')
        
        os.chdir(wps_run_dir)
        args = ' '.join(filelist)
        cmd = '%s/link_grib.csh %s' %(wps_run_dir,args)
        shared.run_cmd(cmd, config)
  
        vtabname = vtable[key]
        prefix = key
        namelist.update('prefix', key)
        namelist.to_file(namelist_wps)
        link_namelist_wps(config)
        vtab_path = wps_dir+'/ungrib/Variable_Tables/'+vtabname
        vtab_wps  = wps_run_dir+'/Vtable'

        if os.path.exists(vtab_wps):
            os.remove(vtab_wps)
        cmd = 'ln -sf %s %s' %(vtab_path, vtab_wps)
        logger.debug(cmd)
        subprocess.call(cmd, shell=True)    
        #logger.debug("changing directory to %s" % wps_run_dir)
        #os.chdir(wps_run_dir)
        cmd     =  '%s/ungrib.exe' % wps_run_dir
        
        logger.debug(cmd)
        shared.run(cmd, config, wps_run_dir)

        cmd = 'grep "Successful completion" %s/ungrib.log*' % wps_run_dir # check for success
        ret =shared.run_cmd(cmd,config)
        if ret!=0:
            raise IOError('ungrib.exe did not complete')
    
    logger.info('*** SUCESS UNGRIB ***')

def run_geogrid(config):
    """ Runs geogrid.exe and checks output was sucessful
    
    Arguments:
    config -- dictionary specifying configuration options
    
    """
    logger =shared.get_logger()
    logger.info("*** RUNINING GEOGRID ***")
    wps_run_dir    = config['wps_run_dir']
    os.chdir(wps_run_dir)

    queue          = config['queue']
    log_file       = '%s/geogrid.log' % wps_run_dir
    
    geogrid_wps = '%(wps_run_dir)s/GEOGRID.TBL' % config

    if not os.path.exists(geogrid_wps):
        raise IOError("Could not find GEOGRID.TBL at: %s " % geogrid_wps)
    

    cmd       =  '%s/geogrid.exe' % wps_run_dir
    
    shared.run(cmd, config, wps_run_dir)
    
    cmd = 'grep "Successful completion" %s/geogrid.log*' %(wps_run_dir)
    ret =shared.run_cmd(cmd, config)
    if ret!=0:
        raise IOError('geogrid.exe did not complete')

    logger.info('*** SUCESS GEOGRID ***')

def run_metgrid(config):
    """ Runs metgrid.exe and checks output was sucessful
    
    Arguments:
    config -- dictionary specifying configuration options
    
    """
    logger =shared.get_logger()
    logger.info("*** RUNNING METGRID ***")
    
    queue          = config['queue']
    wps_run_dir    = config['wps_run_dir']
    log_file       = '%s/metgrid.log' % wps_run_dir
    bdy_conditions = config['bdy_conditions']
    namelist_wps   = config['namelist_wps']
    namelist       = shared.read_namelist(namelist_wps)
    
    met_em_dir     = shared.sub_date(config['met_em_dir'], config['init_time'])        
    
    #
    # vtable may be a dictionary to support running ungrib multiple
    # times. In which case, we need to put multiple prefixes into
    # the namelist.wps file
    #
    
    vtable = config['vtable']
    
    if type(vtable)==type({}):
        prefixes = vtable.keys()
    else:
        prefixes = [bdy_conditions]    

        
    namelist.update('fg_name', prefixes)
    namelist.update('opt_output_from_metgrid_path', met_em_dir, section='metgrid')
    if not config['sst']:
        namelist.remove('constants_name')
        
    namelist.to_file(namelist_wps)
    
    logger.debug('met_em_dir: %s' % met_em_dir)
    if not os.path.exists(met_em_dir):
        logger.debug('creating met_em_dir: %s ' % met_em_dir)
        os.makedirs(met_em_dir)

    os.chdir(wps_run_dir)
    cmd      =  "%s/metgrid.exe" % wps_run_dir
    
    shared.run(cmd, config, wps_run_dir)

    cmd = 'grep "Successful completion" %s/metgrid.log*' % wps_run_dir
    ret =shared.run_cmd(cmd, config)
    if ret!=0:
        raise IOError('metgrid.exe did not complete')
    
    logger.info('*** SUCESS METGRID ***')


def prepare_wrf(config):
    """Checks that met_em files exist, and links into WRF/run directory. 
    
    Arguments:
    config -- a dictionary containing forecast options

    """
    logger =shared.get_logger()    
    logger.debug('*** PREPARING FILES FOR WRF ***')
    
    met_em_format      = "%Y-%m-%d_%H:%M:%S"
    

    max_dom      = config['max_dom']
    domains      = range(1,max_dom+1)
    init_time    = config['init_time']
    fcst_hours   = config['fcst_hours']
    bdy_interval = config['bdy_interval']
    bdy_times    = shared.get_bdy_times(config)
    met_em_dir   = shared.sub_date(config['met_em_dir'], init_time=init_time)
    met_em_files = ['%s/met_em.d%02d.%s.nc' % (met_em_dir,d, t.strftime(met_em_format)) for d in domains for t in bdy_times] 
    wrf_run_dir    = config['wrf_run_dir']
    namelist_run   = '%s/namelist.input' % wrf_run_dir
    namelist_input = config['namelist_input']
    
    
    logger.debug('linking met_em files:')
    
    #
    # Link met_em files. There are two options for error handling here.
    # The first is to abort if any of the met_em files are missing.
    # The second is just to run wrf and see how far it gets before
    # running out of files. This will allow a partial forecast to run, 
    # even if later files are missing.
    #    
    # To use the first approach, raise an exception when a missing
    # file is encountered, otherwise just print a warning message.
    #
    # Actually, the two are equivalent so long as the met_em files 
    # are sorted.
    #
    for f in met_em_files:
        if not os.path.exists(f):
            raise IOError('met_em file missing : %s' %f)
        cmd = 'ln -sf %s %s/'%(f, wrf_run_dir)
        shared.run_cmd(cmd, config)
    
    
    logger.debug('linking namelist.input to wrf_run_dir')
    cmd = 'rm -f %s' % namelist_run
    shared.run_cmd(cmd, config)
    cmd = 'ln -sf %s %s' %(namelist_input, namelist_run)
    shared.run_cmd(cmd, config)

    logger.debug('*** FINISHED PREPARING FILES FOR WRF ***')

def update_namelist_input(config):    
    """ Updates the namelist.input file to reflect updated settings in config.
    Adds a non-standard &metadata section to give a name to the model run
    
    Arguments:
    config -- dictionary containing various configuration options
        
    """        
    logger =shared.get_logger()        
    logger.debug('*** UPDATING namelist.input ***')
    

    #wrf_dir       = config['wrf_dir']
    working_dir   = config['working_dir']
    model         = config['model']
    model_run     = config['model_run']
    
    domain        = config['domain']
        
    namelist_run  = '%s/namelist.input'  % working_dir
    namelist_input = config['namelist_input']
    namelist_wps   = config['namelist_wps']
    shutil.copyfile(namelist_input, namelist_input+'.backup')
    
    # read settings from domain-based namelist
    namelist        = shared.read_namelist(namelist_input)   

    # read settings from domain-based namelist.wps
    #namelist_wps   = shared.read_namelist(namelist_wps)   
    #wps_settings   = namelist_wps.settings


    #
    # Add new metadata section to namelist.input
    #
    logger.debug('Adding metatdata to the namelist.input')
    logger.debug('domain = %s'    %domain)
    logger.debug('model = %s'     %model)
    logger.debug('model_run = %s' %model_run)
    namelist.update('domain', domain, 'metadata')
    namelist.update('model',model, 'metadata')
    namelist.update('model_run',model_run, 'metadata')  

    
    #
    # Overule max_dom with one in config
    #
    max_dom = config['max_dom']
    namelist.update('max_dom', max_dom)
    #logger.debug("Syncing dx and dy between namelist.wps and namelist.input")
    #dx = wps_settings['dx']
    #dy = wps_settings['dy']
    #logger.debug("namleist.wps: dx: %s ------> namelist.input" % dx)
    #logger.debug("namleist.wps: dy: %s ------> namelist.input" % dy)
    #namelist.update('dx', wps_settings['dx'])
    #namelist.update('dy', wps_settings['dy'])    
    fcst_hours       = config['fcst_hours']
    fcst_times       = shared.get_fcst_times(config)
    history_interval = config['history_interval']   
    bdy_interval     = config['bdy_interval']  # this is in hours         
    
    interval_seconds = 60*60*bdy_interval
    
    start   = fcst_times[0]
    end     = fcst_times[-1]
    diff    = end - start
    
    
    #
    # I'm still not sure how the WRF namelist works between 
    # the start and end settings and the run_XX settings.
    # I think we can just keep days as zero, and work entirely
    # in hours
    #
    namelist.update('start_year', [start.year] * max_dom)
    namelist.update('start_month',[start.month]* max_dom)
    namelist.update('start_day',  [start.day]  * max_dom)
    namelist.update('start_hour', [start.hour] * max_dom)
    namelist.update('end_year',   [end.year]   * max_dom)
    namelist.update('end_month',  [end.month]  * max_dom)
    namelist.update('end_day',    [end.day]    * max_dom)
    namelist.update('end_hour',   [end.hour]   * max_dom)
    namelist.update('run_days',   [0])   
    namelist.update('run_hours',  [fcst_hours] )   
    #namelist.update('run_minutes',[0])   
    namelist.update('history_interval', [history_interval] * max_dom)
    namelist.update('interval_seconds', [interval_seconds])


    #
    # If DFI is being used, update DFI settings
    # From user guide:
    # "For time specification, it typically needs to integrate 
    # backward for 0.5 to 1 hour, and integrate forward for half of the time."
    #
    # should we just write this everytime into the file and rely of dfi_opt 
    # as the on/off switch?
    #
    hour         = datetime.timedelta(0, 60*60)
    minute       = datetime.timedelta(0, 60)
    #dfi_bck      = config['dfi_bck'] * minute
    #dfi_fwd      = config['dfi_fwd'] * minute
    #dfi_bckstop  = start - dfi_bck
    #dfi_fwdstop  = start + dfi_fwd
    

    #namelist.update('dfi_bckstop_year',   dfi_bckstop.year,   'dfi_control')
    #namelist.update('dfi_bckstop_month',  dfi_bckstop.month,  'dfi_control')
    #namelist.update('dfi_bckstop_day',    dfi_bckstop.day,    'dfi_control')
    #namelist.update('dfi_bckstop_hour',   dfi_bckstop.hour,   'dfi_control')
    #namelist.update('dfi_bckstop_minute', dfi_bckstop.minute, 'dfi_control')
    #namelist.update('dfi_bckstop_second', dfi_bckstop.second, 'dfi_control')
    #namelist.update('dfi_fwdstop_year',   dfi_fwdstop.year,   'dfi_control')
    #namelist.update('dfi_fwdstop_month',  dfi_fwdstop.month,  'dfi_control')
    #namelist.update('dfi_fwdstop_day',    dfi_fwdstop.day,    'dfi_control')
    #namelist.update('dfi_fwdstop_hour',   dfi_fwdstop.hour,   'dfi_control')
    #namelist.update('dfi_fwdstop_minute', dfi_fwdstop.minute, 'dfi_control')
    #namelist.update('dfi_fwdstop_second', dfi_fwdstop.second, 'dfi_control')
   
    logger.debug('writing new settings to file')
    namelist.to_file(namelist_input)
    
    #logger.debug(namelist)
    logger.debug('*** FINISHED UPDATING namelist.input ***')  

    
def run_real(config):
    """ Run real.exe and check output was sucessful
    Arguments:
    config -- dictionary containing various configuration options """
    
    logger =shared.get_logger()    
    logger.info('*** RUNNING REAL ***')
    
    queue           = config['queue']
    working_dir   = config['working_dir']
    wrf_run_dir     = config['wrf_run_dir']
    wps_dir         = config['wps_dir']
    domain          = config['domain']
    model_run       = config['model_run']
    init_time       = config['init_time']
    log_file        = '%s/real.log' % wrf_run_dir


    # Log files from real appear in the current directory, 
    # so we need to change directory first.
    os.chdir(wrf_run_dir)
    cmd     =  "%s/real.exe" % wrf_run_dir
    shared.run(cmd, config, wrf_run_dir)
    
    
    rsl = '%s/rsl.error.0000' % wrf_run_dir
    if not os.path.exists(rsl):
        raise IOError('No log file found for real.exe')

    # now copy rsl file to a log directory
    cmd = 'cp %s %s/rsl/rsl.error.%s.%s.%s' % (rsl, working_dir, domain, model_run, init_time.strftime('%y-%m-%d_%H') )
    shared.run_cmd(cmd, config)



    cmd = 'grep "SUCCESS COMPLETE" %s/rsl.error.0000' % wrf_run_dir
    ret =shared.run_cmd(cmd, config)
    
    if ret!=0:
        raise IOError('real.exe did not complete')


    logger.info('*** SUCESS REAL ***')


 
def run_wrf(config):
    """ Run wrf.exe and check output was sucessful
    
    Arguments:
    config -- dictionary containing various configuration options
    
    """
    logger          =shared.get_logger()    
    logger.info('*** RUNNNING WRF ***')
    queue         = config['queue']
    wrf_run_dir   = config['wrf_run_dir']
    log_file      = '%s/wrf.log' % wrf_run_dir
    
    executable  = '%s/wrf.exe' % wrf_run_dir
    shared.run(executable, config, wrf_run_dir)
    

    #
    # Check for success
    #    
    cmd = 'grep "SUCCESS COMPLETE" %s/rsl.error.0000' % wrf_run_dir
    ret = shared.run_cmd(cmd, config)
    if ret!=0:
        raise IOError('wrf.exe did not complete')
    
    logger.info('*** SUCESS WRF ***')


def move_wrfout_files(config):
    """ Moves output files from run directory to wrfout 
    director"""
    logger =shared.get_logger()    
    logger.info('*** MOVING WRFOUT FILES AND NAMELIST SETTINGS ***')
    
    domain        = config['domain']
    model_run     = config['model_run']
    working_dir = config['working_dir']
    wrf_run_dir   = config['wrf_run_dir']
    init_time     = config['init_time']
    init_str      = init_time.strftime('%Y-%m-%d_%H')

    namelist_input = config['namelist_input']
    namelist_wps   = config['namelist_wps']
    
    wrfout_dir    = '%s/wrfout'   %(working_dir)
    log_dir       = '%s/log'      % working_dir    
    rsl_dir       = '%s/rsl'      % working_dir
    namelist_dir  = '%s/namelist' % working_dir
    run_key       = '%s.%s'       %(domain, model_run)    # composite key  

    logger.debug('Moving wrfout files from %s to %s' %(wrf_run_dir, wrfout_dir) )

    # Move WRF output files to new directory
    flist = glob.glob(wrf_run_dir+'/wrfout*')
    shared.transfer(flist, wrfout_dir, mode='move', debug_level='debug')

    # Move log files to new directoy
    #flist = glob.glob(wrf_run_dir+'/rsl.*')
    #transfer(flist, rsl_dir, mode='move', debug_level='debug')

    cmd = 'cp %s %s/namelist.input.%s.%s' % (namelist_input, namelist_dir, run_key, init_str)
    shared.run_cmd(cmd, config)
    
    cmd = 'cp %s/namelist.wps %s/namelist.wps.%s.%s' % (working_dir, namelist_dir, run_key, init_str)
    shared.run_cmd(cmd, config)


    #
    # Archive log files
    # 
    logger.debug('moving rsl files to %s' % rsl_dir )
    cmd = 'cp %s/rsl.out.0000 %s/rsl.out.%s' %(wrf_run_dir, rsl_dir, run_key)
    shared.run_cmd(cmd, config)
    

def timing(config):
    """Reads a rsl file from WRF and works out timing information
    from that """

    #
    # Where should we assume to find the rsl file?
    # In the wrf_working_dir
    #
    logger =shared.get_logger()
    logger.info('*** Computing timing information ***')
    wrf_run_dir    = config['wrf_run_dir']
    rsl_file       = '%s/rsl.error.0000' % wrf_run_dir
    namelist_input = config['namelist_input']
    namelist       = shared.read_namelist(namelist_input).settings
    timestep       = namelist['time_step'][0]
    f              = open(rsl_file, 'r')
    lines          = f.read().split('\n')
    
    # get timings on outer domain
    main_times  = [float(l.split()[8]) for l in lines if re.search("^Timing for main: time .* 1:", l)]
    total       = sum(main_times)
    steps       = len(main_times)
    time_per_step = (total/steps)
    x_real       = timestep / time_per_step
    logger.info('*** TIMING INFORMATION ***')
    logger.info('\t %d outer timesteps' % steps)
    logger.info('\t %0.3f elapsed seconds' % total)
    logger.info('\t %0.3f seconds per timestep' % time_per_step )
    logger.info('\t %0.3f times real time' %x_real)
    logger.info('*** END TIMING INFORMATION ***')    
    
    