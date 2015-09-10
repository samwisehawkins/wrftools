import shared

def run_point_stat(config):
    """ Runs the point_stat tool. 
    
    Note that point_stat produces a fixed set of fields. If we want to compare
    outputs from multiple similar runs, we have to make use of one of the fields
    to do this. The 'MODEL' field is probably the most suitable field to use for
    this purpose, but it needs to be set in PointStatConfig, and may interfere with 
    later assumptions when processing mpr_files. The 'VERSION' field is another option.
    
    Arguments:
    config -- dictionary containing various configuration options
    
    """
    
    logger         = get_logger()    
    max_dom        = config['max_dom']
    met_dir        = config['met_dir']
    domain_dir     = config['domain_dir']
    domain         = config['domain']
    dom            = config['dom']        # integer number rather than name
    model          = config['model']
    model_run      = config['model_run']
    bdy_conditions = config['bdy_conditions']
    tmp_dir        = config['tmp_dir']
    ps_config      = config['ps_config'] 
    
    logger.info('*** RUNNING MET POINT STAT ***')
    
    #
    # Generate a tag to write to the 'MODEL' field in mpr files
    #
    wk_dir      = domain_dir
    grb_dir     = '%s/%s/archive' %(domain_dir,model_run)

    fcst_times  = get_fcst_times(config) 
    init_time   = fcst_times[0]
    run_hours   = config['fcst_hours']
   
    grb_file    = '%s/wrfpost_d%02d_%s.grb' %(grb_dir, dom, init_time.strftime('%Y-%m-%d_%H'))
    obs_file    = config['obs_file']

    if not os.path.exists(grb_file):
        raise IOError('could not find file: %s' %grb_file)



    #
    # Stored stat files domain, model run and initial time
    #        
    #out_dir     = '%s/%s/stats/%s/d%02d' %(domain_dir, model_run, init_time.strftime('%Y-%m-%d_%H'), dom)
    out_dir     = '%s/%s/stats' %(domain_dir, model_run)
    out_file    = '%s/%s.%s.%s.d%02d.%s.mpr' %(out_dir, domain, model, model_run, dom, init_time.strftime('%Y-%m-%d_%H'))

    #
    # Write stat files to temporary directory first, then post-process to final directory
    #
    clear_tmp_dir(tmp_dir, config)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    
    #***************************************************
    # Run point_stat
    #**************************************************
    
    #
    # Modify PointStatConfig to ensure model field is correct
    #
    os.chdir(wk_dir)
    cmd = """sed -i'.backup' -e's/^model.*/model  = "%s";/g' %s""" %(model, ps_config)
    run_cmd(cmd, config)
    
    logger.debug('grb: %s' %grb_file)
    logger.debug('obs: %s' %obs_file)
    
    #
    # Remove any existing point-stat files for this initial time
    #
    #logger.debug('removing old point-stat files\n')
    #cmd = 'rm -f %s/point_stat_*_%sV_cnt.txt' %(out_dir, init_time.strftime(ps_format))
    #logger.debug(cmd+'\n')
    #os.system(cmd)
    
    for n,fcst_time in enumerate(fcst_times):
        #
        # Work out decimal number of hours
        #
        logger.debug('processing forecast valid: %s' %fcst_time.strftime(ps_format))
        
        delta   = fcst_time - init_time
        days    = delta.days
        seconds = delta.seconds
        fhr   = 24*days + (seconds / (60.0 * 60.0))
    
        #
        # In the output files, any fractional part is represented by four
        # decimal digits after the first two
        #
        frac_digits = int((fhr - int(fhr))*1000)
        
        logger.debug('calculated lead time: %0.3f hours' % fhr)
        logger.debug('*** EXECUTING POINT STAT ***')

        #
        # Use tmp dir as output directory for now
        #
        #point_stat(met_dir, grb_file, obs_file, tmp_dir, ps_config, fcst_time, fhr)

        cmd = '%s/bin/point_stat %s %s %s -fcst_valid %s -fcst_lead %03d -outdir %s -v 3' %(met_dir, 
                                                                                          grb_file, 
                                                                                          obs_file,
                                                                                          ps_config,
                                                                                          fcst_time.strftime(ps_format),
                                                                                          fhr,
                                                                                          tmp_dir)    
        run_cmd(cmd, config)

        
        #
        # Run sed command to add meta-data
        #
        #run_cmd(cmd, config)       

        
    #
    # Post-process stat files from tmp directory into 
    # output directory.
    # The output files will be standard mpr and .stat files. We can doctor these to add in some 
    # more columns including metadata.
    #
    mpr_files = sorted(glob.glob('%s/*_mpr.txt' % tmp_dir))
    if os.path.exists(out_file):
        os.remove(out_file)
    
    #
    # Write a header? Headers are informative, but can be a pain for concatenating 
    # or importing into databases
    #
    #in_file   = mpr_files[0]
    #cmd = """head -1 %s | awk '{print "DOMAIN MODEL_RUN NEST " $0}' > %s """ % (in_file, out_file)
    #logger.debug(cmd)
    #subprocess.call(cmd, shell=True)
    
    #
    # Process all mpr files. If we want awk to replace mutliple spaces with just one space
    # which is a useful side effect for importing into a database, we must give each field explicitly
    # There are 32 fields in the original mpr files written by MET.
    #
    # This is a bit ugly, and should really get tidied up! 
    # In case anyone else has to make sense of this, here is what is happening.
    # Awk is used to insert extra metadata columns.
    # Awk is then used to print all the remaining fields, seperated by a single space.
    # Sed is used to strip the header line.
    #
    nfields = 31
    for f in mpr_files:
        awk_fields = ' '.join(['" "$%01d' % n for n in range(1, nfields+1)])
        cmd = """awk '{print "%s %s %02d" %s}' %s | sed 1d >> %s """ %(domain, model_run, dom, awk_fields, f, out_file)       
        run_cmd(cmd, config)        
   



    logger.info('*** SUCESS MET POINT STAT ***')





def run_point_stat_gfs(config):
    """ Runs the point_stat tool against GFS output.
    
    This works on the same loop as the other functions, designed to be called 
    once per initial time.
    
    This raises a question as to how we want to archive our GFS files.
    We could store each forecast hour in a seperate file, or we could 
    concatenate all forecast hours into one file per forecast, which may 
    be easier.  
    
    Arguments:
    config -- dictionary containing various configuration options"""
    
    logger      = get_logger()    
    logger.debug('hard coded GFS domain in function: remove')
    
    domain_dir  = '/home/slha/domains/GFS'
    met_dir     = config['met_dir']
    wk_dir      = domain_dir+'/met'
    grb_dir     = config['extract_dir']
    grb_fmt     = config['grb_input_fmt']
    fcst_times  = get_fcst_times(config) 
    init_time   = fcst_times[0]
    run_hours   = config['fcst_hours']
    obs_file    = config['obs_file']
    filelist    = get_bdy_filenames(config)
    ps_config   = domain_dir + '/PointStatConfig'
    for f in filelist:
        logger.debug(f)
    
    #
    # There is no easy way of getting back the initial time from 
    # the point stat files, so we keep them in seperate directions
    #
    out_dir     = '%s/stats/%s' %(domain_dir, init_time.strftime('%Y-%m-%d_%H'))
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    #
    # Remove any existing point-stat files for this valid time
    #
    logger.debug('removing old point-stat files')
    cmd = 'rm -f %s/point_stat_*_%sV_cnt.txt' %(out_dir, init_time.strftime(ps_format))
    #logger.debug(cmd)
    #os.system(cmd)
    
    
    for n,fcst_time in enumerate(fcst_times):
        #
        # Work out decimal number of hours
        #
        logger.debug('processing forecast valid: %s' %fcst_time.strftime(ps_format))
        
        delta   = fcst_time - init_time
        days    = delta.days
        seconds = delta.seconds
        fhr     = 24 * days + (seconds / (60.0 * 60.0))
        
        grb_file = bdy_filename(grb_dir, grb_fmt, init_time, fhr)
        
        
        #
        # Run point_stat
        #
        os.chdir(wk_dir)
        logger.info('*** EXECUTING POINT STAT ***')
        logger.info('grb: %s' %grb_file)
        logger.info('obs: %s' %obs_file)
    
        #
        # In the output files, any fractional part is represented by four
        # decimal digits after the first two
        #
        frac_digits = int((fhr - int(fhr))*1000)
        
        logger.debug('calculated lead time: %0.3f hours' % fhr)
        point_stat(met_dir, grb_file, obs_file, out_dir, ps_config, fcst_time, fhr)
        
        
        cmd = '%s/bin/point_stat %s %s PointStatConfig -fcst_valid %s -fcst_lead %03d -outdir %s -v 3' %(met_dir, 
                                                                                          grb_file, 
                                                                                          obs_file,
                                                                                          fcst_time.strftime(ps_format),
                                                                                          fhr,
                                                                                          out_dir)
        logger.debug(cmd)
        subprocess.call(cmd, shell=True)
    
    return 0    
    
    




def extract_gfs_fields(config):
    """ Creates grib1 extract from GFS based on grib_extract specified in config.
    Calls wgrib2 using egrep to extact fields, then calls 
    grbconv to convert those to grib1 format.
    
    Arguments:
    config -- dictionary containing various configuration options
    
    """
    logger = get_logger()    
    logger.debug('extracting 10m wind to grib1 format')
    #
    # Question is where we store the 
    #
    gribmaster_dir  = config['gribmaster_dir']
    tmp_dir         = config['tmp_dir']
    extract_dir     = config['extract_dir']
    grib_extract    = config['grib_extract']
    tmp_dir         = config['tmp_dir']
    
    clear_tmp_dir(tmp_dir)
    logger.debug('gribmaster_dir: %s' % gribmaster_dir)
    logger.debug('tmp_dir: %s'        % tmp_dir)
    logger.debug('extract_dir: %s'    % extract_dir)
    logger.debug('grib_extract:%s'    % grib_extract)
    
    #
    # Get all boundary conditions associated with this forecast
    #
    bdy_filenames   = get_bdy_filenames(config)
    for f in bdy_filenames:
        name_ext = os.path.split(f)[1]
        parts    = name_ext.split('.')
        name     = parts[0]
        ext      = parts[1]
        
        
        ename = name.replace('Europe', 'Extract')
        epath = '%s/%s' %(extract_dir, ename)
        extract_name = '%s.%s' %(epath, ext)
        
        #
        # Extract the fields based on grid_extract expression
        #
        cmd = 'wgrib2 %s | egrep %s | wgrib2 -i %s -grib %s ' %(f, grib_extract, f, extract_name)
        
        
        logger.debug(cmd)
        subprocess.call(cmd, shell=True)
        grib1_name = '%s.grib1' % epath
        cmd = '%s/bin/cnvgrib -g21 %s %s' %( gribmaster_dir,extract_name,grib1_name) 
        logger.debug(cmd)
        subprocess.call(cmd, shell=True)
    