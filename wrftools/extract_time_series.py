"""extract_time_series.py is a thin wrapper around extract_time_series.ncl which interpolations to locations and heights.

Usage: 
    extract_time_series.py <file>... --loc=<file> --opt=<file> --height=<h>... [--mode=<mode>] [--out=<dir>] [-h | --help] [--ncl-code=<path>] [--dry-run]
    
Options:
    --loc=<file>      locations file containing latitude and longitude
    --out=<dir>       output netcdf file to write time-series
    --opts=<file>     location of a ncl file specifying which variables to extract
    --mode=<mode>     loop: loop over each input file seperately, lump: lump all input files together [default: loop]
    --ncl-code=<path> location of extract_time_series.ncl [default: ./ncl]
    --dry-run         print commands but don't execute
    -h |--help        show this message
    
Notes:
    This requires the extract_time_series.ncl script. 
    
Examples:

    python extract_time_series wrfout_d01_2010-01-* --out=./tseries --netcdf"""

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
