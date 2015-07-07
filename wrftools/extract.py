"""extract.py provides a thin wrapper around an ncl script to 
extract WRF variables and diagnostics at specified locations and
heights above ground level

Usage: 
    extract.py <file>...
              [--config=<file>]
              [--out-dir=<dir>]
              [--ncl-script=<file>]
              [--height=<list>]
              [--loc=<file>]
              [--opt=<file>]
              [--mode=<mode>]
              [--dry-run]
    
Options:
    <file>                  input files to work on
    --config=<file>         configuration file
    --out-dir=<dir>         output directory
    --ncl-script=<file>     location of the ncl script to call, default is ../../extract_time_series.ncl
    --height=<list>         list of heights to extract to
    --loc=<file>            file specifying locations to extract to
    --opt=<file>            ncl file specifying which variables to extract and various ncl options
    --mode=<mode>           loop over input files, or lump input files together
    --dry-run               print commands, don't execute"""

import shared
import confighelper as conf


import os
import sys
import docopt
import subprocess
import time


NCL_SCRIPT = '%s/../ncl/extract_time_series.ncl' % os.path.split(sys.argv[0])[0]
SUPPORTED_MODES = ["loop","lump"]

class ConfigError(Exception):
    pass


def main():         
    """ Pass command line arguments to NCL script"""
    config = conf.config(__doc__, sys.argv[1:])

    t0 = time.time()
    
    if config['out-dir']==None:    
        out_dir = '.'
    else:
        out_dir = config['out-dir']
    
    # if ncl-code-dir not specified, expect it in ../ncl relative to
    # the path of this file
    if config['ncl-script']==None:
        ncl_script = NCL_SCRIPT
    else:
        ncl_code_dir = config['ncl-script']

    cmd_files = config['<file>']
    # Add nc extension if needed
    nc_files = [ f if f.endswith('.nc') else f+'.nc' for f in cmd_files]
   
    # Create height arrays
    hgts = config['height']
    hgts = '(/%s/)' % ','.join(map(str,hgts))
    
    mode = config['mode']
    
    dry_run = config['dry-run']
    
    loc = config['loc']
    opt = config['opt']
    
    
    print '\n*****************************************************'
    print 'extract.py' 
    
    if mode not in SUPPORTED_MODES:
        raise ConfigError("specified mode not supported")
    
    if mode=='loop':
    
        # This will loop over each file seperately
        for f in sorted(nc_files):
            path,name = os.path.split(f)
            out_file = out_dir+'/'+name.replace('wrfout', 'tseries')

            if os.path.exists(out_file):
                os.remove(out_file)
            
            # Create NCL file array
            in_file = f
            #cmd = """FCST_FILE=%s  NCL_OUT_FILE=%s LOCATIONS_FILE=%s NCL_OPT_FILE=%s ncl %s/%s 'extract_heights=%s' """ %(in_file, out_file, loc,opt, ncl_code_dir, NCL_SCRIPT, hgts)
            cmd = """NCL_OPT_FILE=%s ncl 'in_file="%s"' 'out_file="%s"' 'extract_heights=%s' 'loc_file="%s"' %s""" % (opt,in_file,out_file, hgts, loc, ncl_script)
            print cmd
            # We could either aggregate all files together or loop over files
            if not dry_run:
                subprocess.call(cmd, shell=True)
   

    elif mode=='lump':
        f = nc_files[0]
        path,name = os.path.split(f)
        out_file = out_dir+'/'+name.replace('wrfout', 'tseries')
        if os.path.exists(out_file):
            os.rm(out_file)

        
        
        # Create NCL file array
        files = '","'.join(sorted(nc_files))
        in_file = '(/"%s"/)' % files
        cmd = """NCL_OPT_FILE=%s ncl 'in_file=%s' 'out_file="%s"' 'extract_heights=%s' 'loc_file="%s"' %s""" % (opt,in_file,out_file, hgts, loc, ncl_script)
        print cmd
        if not dry_run:
            subprocess.call(cmd, shell=True)

    
    te = time.time() - t0
    print 'elapsed time: %0.1f ' % te

def extract_tseries(config):

    logger = shared.get_logger()
    logger.info('\n*** EXTRACTING TIME SERIES ***')
     
    wrfout_dir     = config['wrfout_dir']
    tseries_dir    = config['tseries_dir']
    json_dir       = config['json_dir']
    init_time      = config['init_time']
    dom            = config['dom']
    fcst_file      = '%s/wrfout_d%02d_%s:00:00.nc' %(wrfout_dir, dom, init_time.strftime("%Y-%m-%d_%H")) # note we add on the nc extension here
    ncl_loc_file   = config['locations_file']
    ncl_code       = config['tseries_code']
    extract_hgts   = config['extract_hgts']
    #tseries_fmt    = config['tseries_fmt']
    ncl_log        = config['ncl_log']
    ncl_opt_template = config['ncl_opt_template']
    ncl_opt_file     = config['ncl_opt_file']

    if not os.path.exists(tseries_dir):
        os.makedirs(tseries_dir)
    
    # Always go via the netcdf file
    tseries_file = '%s/tseries_d%02d_%s.nc' % (tseries_dir, dom,init_time.strftime("%Y-%m-%d_%H"))

    ncl_hgts = '(/%s/)' % ','.join(map(str,extract_hgts))
    replacements = {'<ncl_in_file>'  : fcst_file, 
                    '<ncl_out_file>' : tseries_file,
                    '<ncl_out_dir>'  : tseries_dir, 
                    '<ncl_out_type>' : "nc",
                    '<ncl_loc_file>' : ncl_loc_file,
                    '<extract_heights>': ncl_hgts}
        

    shared.fill_template(ncl_opt_template, ncl_opt_file, replacements)
        
    logger.debug('ncl_opt_template: %s' % ncl_opt_template)
    logger.debug('    ncl_in_file  ----> %s' % fcst_file)
    logger.debug('    ncl_out_dir  ----> %s' % tseries_dir)
    logger.debug('    ncl_out_type ----> %s' % "nc")
    logger.debug('    ncl_loc_file ----> %s' % ncl_loc_file)
    logger.debug('ncl_opt_file: %s' % ncl_opt_file)
    
    
    
    for script in ncl_code:
        cmd  = "NCL_OPT_FILE=%s ncl %s >> %s 2>&1" % (ncl_opt_file,script, ncl_log)
        shared.run_cmd(cmd, config)

    logger.info("*** DONE EXTRACTING TIME SERIES ***\n")
    
if __name__ == '__main__':
    main()
    