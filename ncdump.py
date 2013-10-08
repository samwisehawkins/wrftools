"""ncdump.py dumps data from a netcdf file to text file

Usage: 
    ncdump.py <file>... [--dims=<dimspec>]... [--out=<dir>] [-h | --help]
    
Options:
    --out=<dir>       output directory to write time-series
    -h |--help        show this message
    
Notes:
    Currently the file format is fixed
    
Examples:

    python ncdump.py wrfout_d01_2010-01-* --out=./tseries """

import sys
import docopt
import subprocess
import datetime
from netCDF4 import Dataset
from netCDF4 import num2date, date2num

COORD_VARS      = ['time', 'height', 'location', 'lat', 'lon']
FILE_DATE_FMT   = '%Y-%m-%d_%H%M'  # Date format for file name
DATE_FMT        = '%Y-%m-%d %H:%M' # Date format within files



def main():         
    """ Pass command line arguments to NCL script"""
    args = docopt.docopt(__doc__, sys.argv[1:])

    print '\n********************************'
    print 'dumping netCDF time series to flat files'
    ncfiles = args['<file>']
    
    if args['--out']==None:
        out_dir = '.'
    else:
        out_dir = args['--out']

    dims = args['--dims']

    write_seperate_files(ncfiles, out_dir, dims)
        

def write_columns(ncfiles, fname):
    """Writes each variable and height into a seperate column"""
    pass
    
    
def write_seperate_files(ncfiles, out_dir, dims):        
    """ Writes each variable and height into a seperate text file"""

    # time, location and height start and end indices
    ts = 0
    te = None
    ls = 0
    le = None
    hs = 0
    he = None
    for dim in dims:
        d,s,e = dim.split(',')
        if d=='time':
            ts = int(s)
            te = int(e)
        if d=='location':
            ls = int(s)
            le = int(e)
        if d=='height':
            hs = int(s)
            he = int(e)
    

    for f in ncfiles:
        dataset = Dataset(f, 'r')
        
        # get some global attributes
        model     = dataset.MODEL
        nest_id   = dataset.GRID_ID
        model_run = dataset.MODEL_RUN
        domain    = dataset.DOMAIN
        
        variables = dataset.variables
        fulltime      = variables['time']
        fulldatetimes = num2date(fulltime,units=fulltime.units,calendar=fulltime.calendar)
        
        time      = fulltime[ts:te]
        datetimes = fulldatetimes[ts:te]
        
        init_time = fulldatetimes[0]
        location  = variables['location'][ls:le]
        height    = variables['height']

        
        lat       = variables['lat'][ls:le]
        lon       = variables['lon'][ls:le]
        
        ntimes    = len(time)
        nlocs     = location.shape[0]
        loc_str_len = location.shape[1]
        

        for v in variables:
            # skip coordinate variables
            if v in COORD_VARS:
                continue
            
            fullvar = variables[v]
            ndims = len(fullvar.shape)
            
            # 2D variable, variable[time, location]
            if ndims==2:
                var = fullvar[ts:te, ls:le]
            
            if ndims==3:
                var = fullvar[ts:te, ls:le, hs:he]
            
            
            for l in range(nlocs):
                loc = ''.join(location[l,0:loc_str_len-1])
                loc = loc.strip()
                
                # 2D variable
                if ndims==2:
                    hgts = [0.0]
                # 3D variable
                elif ndims==3:
                    hgts = height[hs:he]
                
                print '\n\nprocessing 3D variable'
                print 'height', hgts
                print height
                print hs, he

                    
                for h in range(len(hgts)):
                    hgt = hgts[h]
                    fname = '%s/%s_%s_d%02d_%03d_%s.txt' % (out_dir, loc, v, nest_id, int(hgt), init_time.strftime(FILE_DATE_FMT))
                    fout = open(fname, 'w')
                    fout.write('domain,model_run,model,nest_id,location_id,latitude,longitude,variable,init_time,valid_time,height,value\n')
                    for t in range(ntimes):
                        valid_time = datetimes[t].strftime(DATE_FMT)
                        if ndims==2:
                            val = var[t,l]
                        elif ndims==3:
                            val = var[t,l, h]
                        line = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%03d,%0.3f\n' %(domain, model_run, model,nest_id,loc, lat[l], lon[l], v, init_time.strftime(DATE_FMT), valid_time, hgt, val)
                        fout.write(line)
        
                    fout.close()
        
        dataset.close()

    
if __name__ == '__main__':
    main()

