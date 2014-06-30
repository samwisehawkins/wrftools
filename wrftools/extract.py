import shared
from ncdump import ncdump 

import os
import sys
import docopt
import subprocess
import time


NCL_SCRIPT = 'extract_time_series.ncl'


def main():         
    """ Pass command line arguments to NCL script"""
    args = docopt.docopt(__doc__, sys.argv[1:])

    t0 = time.time()
    
    if args['--out']==None:    
        out_dir = '.'
    else:
        out_dir = args['--out']
    
    
    if args['--ncl-code']==None:
        fullpath = os.path.realpath(sys.argv[0])
        p,f = os.path.split(fullpath)
        ncl_code_dir = '%s/ncl'% p
    else:
        ncl_code_dir = args['--ncl-code']

    cmd_files = args['<file>']
    # Add nc extension if needed
    nc_files = [ f if f.endswith('.nc') else f+'.nc' for f in cmd_files]
   
    # Create height arrays
    hgts = args['--height']
    hgts = '(/%s/)' % ','.join(hgts)
    
    mode = args['--mode']
    
    dry_run = args['--dry-run']
    
    loc = args['--loc']
    opt = args['--opt']
    
    
    print '\n*****************************************************'
    print 'extract_time_series.py' 
    print args
    
    if mode=='loop':
    
        # This will loop over each file seperately
        for f in sorted(nc_files):
            path,name = os.path.split(f)
            out_file = out_dir+'/'+name.replace('wrfout', 'tseries')

            if os.path.exists(out_file):
                os.rm(out_file)
            
            # Create NCL file array
            in_file = f
            #cmd = """FCST_FILE=%s  NCL_OUT_FILE=%s LOCATIONS_FILE=%s NCL_OPT_FILE=%s ncl %s/%s 'extract_heights=%s' """ %(in_file, out_file, loc,opt, ncl_code_dir, NCL_SCRIPT, hgts)
            cmd = """NCL_OPT_FILE=%s ncl 'in_file="%s"' 'out_file="%s"' 'extract_heights=%s' 'loc_file="%s"' %s/%s""" % (opt,in_file,out_file, hgts, loc, ncl_code_dir, NCL_SCRIPT)
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
        cmd = """NCL_OPT_FILE=%s ncl 'in_file=%s' 'out_file="%s"' 'extract_heights=%s' 'loc_file="%s"' %s/%s""" % (opt,in_file,out_file, hgts, loc, ncl_code_dir, NCL_SCRIPT)
        print cmd
        if not dry_run:
            subprocess.call(cmd, shell=True)

    
    te = time.time() - t0
    print 'elapsed time: %0.1f ' % te
if __name__ == '__main__':
    main()

def extract_tseries(config):

    logger = shared.get_logger()
    logger.info('*** EXTRACTING TIME SERIES ***')
     
    wrfout_dir     = config['wrfout_dir']
    tseries_dir    = config['tseries_dir']
    json_dir       = config['json_dir']
    init_time      = config['init_time']
    dom            = config['dom']
    fcst_file      = '%s/wrfout_d%02d_%s:00:00.nc' %(wrfout_dir, dom, init_time.strftime("%Y-%m-%d_%H")) # note we add on the nc extension here
    loc_file       = config['locations_file']
    ncl_code       = config['tseries_code']
    extract_hgts   = config['extract_hgts']
    tseries_fmt    = config['tseries_fmt']
    ncl_opt_file   = config['ncl_opt_file']
    
    
    ncl_log        = config['ncl_log']
    if not os.path.exists(tseries_dir):
        os.makedirs(tseries_dir)
    
    # Always go via the netcdf file
    tseries_file = '%s/tseries_d%02d_%s.nc' % (tseries_dir, dom,init_time.strftime("%Y-%m-%d_%H"))

    os.environ['FCST_FILE']      = fcst_file
    os.environ['LOCATIONS_FILE'] = loc_file
    os.environ['NCL_OUT_DIR']    = tseries_dir
    os.environ['NCL_OUT_FILE']   = tseries_file
    os.environ['NCL_OPT_FILE']   = ncl_opt_file
    
    
    logger.debug('Setting environment variables')
    logger.debug('FCST_FILE    ----> %s'  % fcst_file)
    logger.debug('NCL_OUT_DIR  ----> %s'  % tseries_dir)
    logger.debug('NCL_OUT_FILE  ----> %s' % tseries_file)
    logger.debug('LOCATIONS_FILE ----> %s' % loc_file)
    logger.debug('NCL_OPT_FILE   ----> %s' % ncl_opt_file)
    logger.debug(extract_hgts)

    ncl_hgts = '(/%s/)' % ','.join(map(str,extract_hgts))
    
    for script in ncl_code:
        cmd  = "ncl 'extract_heights=%s'  %s >> %s 2>&1" % (ncl_hgts,script, ncl_log)
        shared.run_cmd(cmd, config)

    ncdump(config)