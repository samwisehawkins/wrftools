import os
import shared


def compress(config):
    """Compresses netcdf files to netcdf4 format. Relies on 
    the NCO operator nccopy.  Will try and compress all output netcdf files
    associated with the current initial time, based on the standard WRF naming 
    convention.  If a simulation produces multiple wrfout files for an
    initial time (i.e. one file per day for three days), then only the first file
    will be compressed under the current configuration.
    
    nccopy does not support the -O overwrite flag, so we need to manually rename the files,
    and remove the originals on sucess"""
    
    logger=shared.get_logger()
    logger.info("*** Compressing wrfout files ***")
    wrfout_dir = config['wrfout_dir']
    init_time  = config['init_time']
    max_dom    = config['max_dom']
    comp_level = config['compression_level']
    
    
    wrfout_files = ['%s/wrfout_d%02d_%s' %(wrfout_dir, d, init_time.strftime('%Y-%m-%d_%H:%M:%S')) for d in range(1,max_dom+1)]
    for f in wrfout_files:
        if not os.path.exists(f):
            raise MissingFile("could not find %s" % f)
        tmp_name = f + '.tmp'
        logger.debug("compressing %s to temporary file: %s" % (f, tmp_name))
        cmd = 'nccopy -k4 -d %s %s %s' %(comp_level, f, tmp_name)
        shared.run(cmd, config)
        if not os.path.exists(tmp_name):
            raise IOError("compression failed for %s" % f)
        
        os.remove('%s' %f)
        os.rename(f+'.tmp', f) 
    
    logger.info("*** Done compressing wrfout files ***")        

    
def hyperslab(config):
    
    logger=shared.get_logger()
    logger.info("*** Hyperslabbing wrfout files ***")
    wrfout_dir = config['wrfout_dir']
    init_time  = config['init_time']
    max_dom    = config['max_dom']
    dimspec    = config['post.hyperslab.dimspec']
    
    
    wrfout_files = ['%s/wrfout_d%02d_%s' %(wrfout_dir, d, init_time.strftime('%Y-%m-%d_%H:%M:%S')) for d in range(1,max_dom+1)]
    for f in wrfout_files:
        if not os.path.exists(f):
            raise MissingFile("could not find %s" % f)
        tmp_name = f + '.tmp'
        logger.debug("compressing %s to temporary file: %s" % (f, tmp_name))
        cmd = 'ncks -4 -O %s %s %s' % (dimspec, f, tmp_name)
        shared.run(cmd, config)
        if not os.path.exists(tmp_name):
            raise IOError("compression failed for %s" % f)
        
        os.remove('%s' %f)
        os.rename(f+'.tmp', f) 
    
    logger.info("*** Done hyperslabbing wrfout files ***")       
    
    
    
def add_metadata(config):
    """ Adds metadata tags into the wrfout files. Expects there to be one 
    wrfout file per init_time. If there are more, they will not have metadata added."""

    logger = shared.get_logger()
    logger.info("*** Adding metadata to wrfout files ***")


    wrfout_dir = config['wrfout_dir']
    init_time  = config['init_time']
    max_dom    = config['max_dom']
    
    metadata = config['metadata']
    logger.debug(metadata)
    wrfout_files = ['%s/wrfout_d%02d_%s' %(wrfout_dir, d, init_time.strftime('%Y-%m-%d_%H:%M:%S')) for d in range(1,max_dom+1)]
    
    for f in wrfout_files:
        logger.debug("compressing %s" % f)
        if not os.path.exists(f):
            raise MissingFile("could not find %s" % f)
        
        # create attribute description for ncatted 
        # note that we make the attribute names uppercase for consistency with WRF output
        att_defs = ' '.join(['-a %s,global,c,c,"%s"' %(s.upper(), config[s]) for s in metadata])
        logger.debug(att_defs)
        cmd = 'ncatted -O -h %s %s' % (att_defs, f)
        logger.debug(cmd)
        shared.run_cmd(cmd, config)
    
    
    
def run_unipost(config):
    """ Runs the Universal Post Processor for each forecast time. 
    Translated from the run_unipost_frames shell script. A post-processing
    directory should exist, specified by the post_dir entry in config, and
    the UPP control file wrf_cntrl should exist within this directory.
    
    TODO: tidy up some of the hangovers from the shell script version
    
    Arguments:
    config -- dictionary containing various configuration options
    
    """
    logger = shared.get_logger()    
    logger.info('*** RUNNING UNIVERSAL POST PROCESSOR ***')
    
    domain_dir    = config['domain_dir']
    max_dom       = config['max_dom']
    dom           = config['dom'] # current domain number
    model_run     = config['model_run']
    wrfout_dir    = '%s/%s/wrfout' %(domain_dir, model_run)    


    post_dir      = '%s/%s/postprd' % (domain_dir, model_run)
    wrf_cntrl     = post_dir+'/wrf_cntrl.parm'
    upp_dir       = config['upp_dir']
    wrf_working_dir   = config['wrf_dir']+'/run'
    namelist      = read_namelist(wrf_working_dir+'/namelist.input')

    fcst_times    = get_fcst_times(config)    
    init_time     = fcst_times[0]
    history_interval = config['history_interval']
    grb_fmt       = config['grb_fmt']


    #----CREATE DIRECTORIES-----------------------------------------------
    # Create archive directories to store data and settings
    #---------------------------------------------------------------------


    wrfpost_dir    = '%s/%s/wrfpost' %(domain_dir,model_run)

    if not os.path.exists(wrfpost_dir):
        os.makedirs(wrfpost_dir)

    #----PREPARATION-------------------------------------------------------
    # Link all the relevant files need to compute various diagnostics
    #---------------------------------------------------------------------
    
    #
    # Everything is done within the postprd directory
    #
    logger.debug('Going into postprd directory: %s' %post_dir)
    #os.chdir(post_dir)

    #
    # Clean up old output files
    #
    #logger.debug('Removing old output files')
    cmd = 'rm -f %s/*.out' % post_dir
    shared.run_cmd(cmd, config)
    cmd = 'rm -f %s/*.tm00' % post_dir
    shared.run_cmd(cmd, config)
    
    
    # Link Ferrier's microphysic's table and Unipost control file, 
    cmd = 'ln -sf %s/ETAMPNEW_DATA ./eta_micro_lookup.dat' % wrf_working_dir
    shared.run_cmd(cmd, config)
    
    #
    # Get local copy of parm file
    # no - lets force the user to manually ensure a copy is placed
    # in the postprd diretory first
    # os.system('ln -sf ../parm/wrf_cntrl.parm .')
    
    #
    # Check wrf_cntrl file exists
    #
    if not os.path.exists(wrf_cntrl):
        raise IOError('could not find control file: %s'% wrf_cntrl)
    
    
    #
    # link coefficients for crtm2 (simulated GOES)
    # Jeez - these should really get called via run_cmd for 
    # consistency, but I can't be chewed right now
    #
    CRTMDIR  = upp_dir+'/src/lib/crtm2/coefficients'
    os.system('ln -fs %s/EmisCoeff/Big_Endian/EmisCoeff.bin           ./' %CRTMDIR)
    os.system('ln -fs %s/AerosolCoeff/Big_Endian/AerosolCoeff.bin     ./' %CRTMDIR)
    os.system('ln -fs %s/CloudCoeff/Big_Endian/CloudCoeff.bin         ./' %CRTMDIR)
    os.system('ln -fs %s/SpcCoeff/Big_Endian/imgr_g12.SpcCoeff.bin    ./' %CRTMDIR)
    os.system('ln -fs %s/TauCoeff/Big_Endian/imgr_g12.TauCoeff.bin    ./' %CRTMDIR)
    os.system('ln -fs %s/SpcCoeff/Big_Endian/imgr_g11.SpcCoeff.bin    ./' %CRTMDIR)
    os.system('ln -fs %s/TauCoeff/Big_Endian/imgr_g11.TauCoeff.bin    ./' %CRTMDIR)
    os.system('ln -fs %s/SpcCoeff/Big_Endian/amsre_aqua.SpcCoeff.bin  ./' %CRTMDIR)
    os.system('ln -fs %s/TauCoeff/Big_Endian/amsre_aqua.TauCoeff.bin  ./' %CRTMDIR)
    os.system('ln -fs %s/SpcCoeff/Big_Endian/tmi_trmm.SpcCoeff.bin    ./' %CRTMDIR)
    os.system('ln -fs %s/TauCoeff/Big_Endian/tmi_trmm.TauCoeff.bin    ./' %CRTMDIR)
    os.system('ln -fs %s/SpcCoeff/Big_Endian/ssmi_f15.SpcCoeff.bin    ./' %CRTMDIR)
    os.system('ln -fs %s/TauCoeff/Big_Endian/ssmi_f15.TauCoeff.bin    ./' %CRTMDIR)
    os.system('ln -fs %s/SpcCoeff/Big_Endian/ssmis_f20.SpcCoeff.bin   ./' %CRTMDIR)
    os.system('ln -fs %s/TauCoeff/Big_Endian/ssmis_f20.TauCoeff.bin   ./' %CRTMDIR)
    
    os.putenv('MP_SHARED_MEMORY', 'yes')
    os.putenv('MP_LABELIO', 'yes')
    os.putenv('tmmark', 'tm00')
    
    
    #
    # Run unipost for each time in the output file
    # Note that unipost names the intermediate files
    # WRFPRShhh.tm00 where hhh is the forecast hour
    #
    for n,t in enumerate(fcst_times):
    
        current_time = t.strftime('%Y-%m-%d_%H:%M:%S')
        fhr          = n*history_interval/60
        #logger.debug('post processing time %s, fhr %d ' % (current_time, fhr))

        #
        # Assume the forecast is contained in one wrfout file 
        # named according to the forecast initial time
        #
        wrfout = '%s/wrfout_d%02d_%s' %(wrfout_dir,dom, init_time.strftime('%Y-%m-%d_%H:%M:%S'))
        #logger.debug('looking for file: %s' % wrfout)
        
        #--- itag file --------------------------------------------------------
        #   Create input file for Unipost
        #   First line is where your wrfout data is
        #   Second line is the format
        #   Third line is the time for this process file
        #   Forth line is a tag identifing the model (WRF, GFS etc)
        #----------------------------------------------------------------------
        #logger.debug('writing itag file')
        #logger.debug('time in itag file: %s' %current_time)
        itag = open('itag', 'w')
        itag.write('%s\n'%wrfout)
        itag.write('netcdf\n')
        itag.write('%s\n'%current_time)
        itag.write('NCAR\n')
        itag.close()
        
        #-----------------------------------------------------------------------
        #  Check wrf_cntrl.parm file exists
        #-----------------------------------------------------------------------            
        
        
        
        #-----------------------------------------------------------------------
        #   Run unipost.
        #-----------------------------------------------------------------------            
        os.system('rm -f fort.*')
        os.system('ln -sf wrf_cntrl.parm fort.14')
        os.system('ln -sf griddef.out fort.110')
        cmd = '%s/bin/unipost.exe < itag > unipost_d%02d.%s.out 2>&1' %(upp_dir, dom,current_time)
        shared.run_cmd(cmd, config)
        
        tmp_name = 'WRFPRS%03d.tm00' % fhr
        grb_name = 'wrfpost_d%02d_%s.tm00' %(dom,current_time)
        
        #
        # If keeping same format, just move output file
        #
        cmd = 'mv %s %s' %(tmp_name, grb_name)
        shared.run_cmd(cmd, config)
        
        #
        # Convert to grib2 format if required
        #            
        #if grb_fmt=='grib2':
        #    cmd = 'cnvgrib -g12 %s %s' %(tmp_name, grb_name) 
        #    shared.run_cmd(cmd, config)
            
    logger.debug('concatenating grib records into single file for domain dom %02d...' %dom)
    outname = 'wrfpost_d%02d_%s.grb'%(dom,init_time.strftime('%Y-%m-%d_%H'))
    cmd     = 'cat wrfpost_d%02d_*.tm00 > %s' %(dom, outname)
    shared.run_cmd(cmd, config)

    
    #-----------------------------------------------------------------------
    # Archive
    #-----------------------------------------------------------------------
    cmd = 'mv %s %s' %(outname, wrfpost_dir)

    ret = shared.run_cmd(cmd, config)
    
    if ret!=0:
        raise IOError('could not move post-processed output')
  
  
    logger.info("*** SUCESS UPP ***")


def convert_grib(config):
    """Converts the grib1 outputs of UPP to grib2 format, mainly so the wgrib2 tool 
    can be used to extract csv time series from it.
    
    
    Should not rely on globbing directories here. Could have nasty consequences,
    e.g. conversion of too many files etc """

    logger=shared.get_logger()
    logger.debug('*** CONVERTING GRIB1 TO GRIB2 ***')
    domain_dir = config['domain_dir']
    model_run  = config['model_run']
    init_time  = config['init_time']
    dom        = config['dom']
    
    
    
    f1 = '%s/%s/archive/wrfpost_d%02d_%s.grb' % (domain_dir, model_run, dom, init_time.strftime('%Y-%m-%d_%H'))
    f2 =  f1.replace('.grb', '.grib2')
    cmd = 'cnvgrib -g12 %s %s' %(f1, f2)
    shared.run_cmd(cmd, config)
    
    