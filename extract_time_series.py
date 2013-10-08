"""extract_time_series.py is a thin wrapper around extract_time_series.ncl which interpolations to locations and heights.

Usage: 
    extract_time_series.py <file>... --loc=<file> --height=<h>... [--out=<dir>] --domain=<dom> --model-run=<run>  [-h | --help] [--ncl-code=<path>] [--loop | --aggregate]
    
Options:
    --loc=<file>      locations file containing latitude and longitude
    --out=<file>      output netcdf file to write time-series
    --text=<dir>      optionally dump flat text files to this directory
    --domain=<dom>    string describing the model domain
    --model-run=<run> string describing the model run
    --ncl-code=<path> location of extract_time_series.ncl [default: ./ncl]
    -h |--help        show this message
    
Notes:
    This requires the extract_time_series.ncl script. Currently the variables extracted,the heights,
    and the file-naming conventions are hard-coded in that script.
    
Examples:

    python extract_time_series wrfout_d01_2010-01-* --out=./tseries --netcdf"""

import os
import sys
import docopt
import subprocess


NCL_SCRIPT = 'extract_time_series.ncl'


def main():         
    """ Pass command line arguments to NCL script"""
    args = docopt.docopt(__doc__, sys.argv[1:])

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
    

    # Try and lump all files together and let NCL open with addFiles
    # Name output file from first file in list
    if args['--aggregate']:
        f,n = os.path.split(nc_files[0])
        out_file = out_dir+'/'+n.replace('wrfout', 'tseries')


        # Create NCL file array
        in_file = '(/"%s"/)' % '","'.join(nc_files)

        cmd = """ncl 'in_file=%s' 'out_file="%s"' 'extract_heights=%s' 'loc_file="%s"' 'domain="%s"' 'model_run="%s"' %s/%s""" % (in_file,out_file,hgts, args['--loc'], args['--domain'], args['--model-run'], ncl_code_dir, NCL_SCRIPT)
        print cmd
        subprocess.call(cmd, shell=True)
    
    # Loop over input files seperately
    if args['--loop']:
        for f in nc_files:
            path,name = os.path.split(f)
            out_file = out_dir+'/'+name.replace('wrfout', 'tseries')

            # Create NCL file array
            in_file = '(/"%s"/)' % f
            cmd = """ncl 'in_file=%s' 'out_file="%s"' 'extract_heights=%s' 'loc_file="%s"' 'domain="%s"' 'model_run="%s"' %s/%s""" % (in_file,out_file,hgts, args['--loc'], args['--domain'], args['--model-run'], ncl_code_dir, NCL_SCRIPT)
            print cmd
            # We could either aggregate all files together or loop over files
            subprocess.call(cmd, shell=True)
    
    
    
if __name__ == '__main__':
    main()
