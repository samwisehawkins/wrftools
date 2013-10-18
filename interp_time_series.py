"""interp_time_series.py is a basic interpolation and extraction script which interpolates wind speed and direction to locations and heights.
Only nearest neighbour interpolation is used, i.e. the value from the centre of the grid cell containing the location

Usage: 
    interp_time_series.py <file>... --loc=<file> --height=<h1,h2,...,hn>... --atts=<attributes> [--dims=<dimspec>]... [--out=<dir>] [-h | --help] 
    
Options:
    --loc=<file>      locations file containing latitude and longitude
    --height=<h1,h2,...,hn> comma seperated list of heights to interpolate to
    --atts=<attributes>  list of attributes  to write to time-series, in form key1:value1,key2:value2. If value is left 
                         blank, will attempt to use value of global attribute from netcdf file
    --dims=<dimspec>
    --out=<dir>          output directory to write time-series, d
    
    -h |--help        show this message
    
Notes:
    This requires the extract_time_series.ncl script. Currently the variables extracted,the heights,
    and the file-naming conventions are hard-coded in that script.
    
Examples:

    python extract_time_series wrfout_d01_2010-01-* --out=./tseries --netcdf"""

import sys    
import time
import datetime
import numpy as np
import wrftools
import tools
import docopt
from customexceptions import DomainError
from netCDF4 import Dataset
from collections import OrderedDict

# This should correspond to the header of the locations file
DTYPE = [('location_id', 'S6'), ('name', 'S10'), ('country', 'S10'), ('hubheight', '<f8'),('latitude', '<f8'),('longitude', '<f8')]



def main():         

    
    args = docopt.docopt(__doc__, sys.argv[1:])

    # Read locations file
    locfile = args['--loc']
    locations = read_loc_file(locfile, DTYPE)

    # Default to current directory if no output directory specified
    if args['--out']==None:    
        out_dir = '.'
    else:
        out_dir = args['--out']

    # Get wrfout files to operate on    
    nc_files = args['<file>']
    
    # Create height arrays to interpolate to
    hgts = args['--height'][0].split(',')
    interp_height = np.array(map(float,hgts))

    # Fetch dimension slicing specs
    dims = args['--dims']
   
    ts = 0     # time start
    te = None  # time end, None uses all times
    for dim in dims:
        d,s,e = dim.split(',')
        if d=='time':
            ts = int(s)
            te = int(e)
    
    # For each file
    for f in nc_files:
        dataset = Dataset(f, 'r')

        # Get attributes to write to time-series
        atts = OrderedDict()
        for a in args['--atts'].split(','):
            keyval = a.split(':')
            if len(keyval)==1:
                key = keyval[0]
                atts[key.lower()] = dataset.getncattr(key)
            else:
                atts[keyval[0]] = keyval[1]

        
        # Get some dimensions
        dims              = dataset.dimensions
        west_east         = dims['west_east']
        west_east_stag    = dims['west_east_stag']
        south_north       = dims['south_north']
        south_north_stag  = dims['south_north_stag']
        bottom_top        = dims['bottom_top']  
        bottom_top_stag   = dims['bottom_top_stag']
        
        # WRF times are a chararcter array, convert them into datetimes
        times     = dataset.variables['Times']

        
        tstrings = [''.join(t) for t in times]
        dtimes   = [datetime.datetime(*time.strptime(t,'%Y-%m-%d_%H:%M:%S')[0:5]) for t in tstrings]
        init_time = dtimes[0]
        
        # allow subsetting of time
        use_times = dtimes[ts:te]
        ntimes    = len(use_times)
        
        lat2d = dataset.variables['XLAT'][0,:,:]
        lon2d = dataset.variables['XLONG'][0,:,:]

        ph     = dataset.variables['PH'][:]
        phb    = dataset.variables['PHB'][:]
        hgt    = dataset.variables['HGT'][:]
        u      = dataset.variables['U'][:]
        v      = dataset.variables['V'][:]
            
        
        #
        # Destagger wind speeds to mass points
        #
        um = 0.5*(u[:,:,:,0:len(west_east)] + u[:,:,:,1:len(west_east_stag)])
        vm = 0.5*(v[:,:,0:len(south_north),:] + v[:,:,1:len(south_north_stag),:])
    
    
        #
        # calculate height of staggered, then unstaggered levels
        #
        stag_heights =  (ph + phb) / 9.81
        mass_heights = 0.5*(stag_heights[:,0:len(bottom_top),:,:] + stag_heights[:,1:len(bottom_top_stag),:,:])
    
        #
        # Work out height above ground level by subtracting terrain height
        #
        agl_heights = mass_heights - hgt[:,np.newaxis,:,:]
       
        #
        # Now loop through each location in the file and extract time-series for that point
        #
        for l in locations :
            loc_id = l['location_id']
            lat    = l['latitude']
            lon    = l['longitude']
            
            # find nearest grid point
            (x,y, dist) = get_index(lat, lon, lat2d, lon2d)            
            
            # get heights at this point
            level_heights = agl_heights[:,:,y,x]            
            
            # loop over heights. 
            # there may be a more pythonic way to do this without looping
            for i_hgt in interp_height:
                speed_fname = '%s/%s_SPEED_d%02d_%03d_%s.txt' %(out_dir, loc_id, atts['grid_id'], int(i_hgt), init_time.strftime('%Y-%m-%d_%H%M'))
                dir_fname   = '%s/%s_DIRECTION_d%02d_%03d_%s.txt' %(out_dir, loc_id,atts['grid_id'], int(i_hgt), init_time.strftime('%Y-%m-%d_%H%M'))
                
                speed_file = open(speed_fname, 'w')
                dir_file = open(dir_fname, 'w')
                
                # find capping level
                levels_above  = np.argmax(level_heights>=i_hgt, axis=1)
                levels_below = levels_above - 1

                #
                # If levels_above contains a zero, it means a height has been requested which 
                # is below the lowest model level, and interpolation will fail
                #
                if np.min(levels_above)==0:
                    raise InterpolationError('height requested is below lowest model level, interpolation will fail')

                #
                # Make the simplifying assumption that the capping level 
                # doesn't change during the course of a file, typically one day
                # This is almost always justified, as the heights of model levels varies 
                # only very slightly (.1m), and it simplifies the code significnatly
                #
                level_above = levels_above[0]
                level_below = levels_below[0]

                hgt_above    = level_heights[:,level_above]
                hgt_below    = level_heights[:,level_below]
                hgt_diff     = hgt_above - hgt_below
            
                # What proportion of the level thickness are we below the upper capping level?
                height_frac = (hgt_above - i_hgt) / hgt_diff
        
                u_above = um[:,level_above,y,x]
                u_below = um[:,level_below,y,x]
                u_diff  = u_above - u_below
        
                v_above = vm[:,level_above,y,x]
                v_below = vm[:,level_below,y,x]
                v_diff  = v_above - v_below

                #
                # Do the linear interpolation
                #
                interp_u = u_above - (height_frac * u_diff)
                interp_v = v_above - (height_frac * v_diff)
                
                speed     = np.sqrt(interp_u**2+interp_v**2)
                direction = tools.bearing(interp_u, interp_v) 
                
                att_header = ','.join(atts.keys())
                att_values = ','.join(map(str,atts.values()))

                header = att_header+',location_id,latitude,longitude,variable,init_time,valid_time,height,value'
                speed_file.write(header)
                dir_file.write(header)
                speed_file.write('\n')
                dir_file.write('\n')

                for n in range(ntimes):
                    speed_file.write('%s,%s,%0.6f,%0.6f,%s,%s,%s,%0.3f,%0.3f\n' % (att_values, loc_id, lat, lon, 'SPEED', init_time.strftime('%Y-%m-%d %H:%M'), dtimes[ts+n].strftime('%Y-%m-%d %H:%M'), i_hgt, speed[ts+n]))
                    dir_file.write('%s,%s,%0.6f,%0.6f,%s,%s,%s,%0.3f,%0.3f\n' % (att_values, loc_id, lat, lon, 'DIRECTION', init_time.strftime('%Y-%m-%d %H:%M'), dtimes[ts+n].strftime('%Y-%m-%d %H:%M'), i_hgt, direction[ts+n]))                    
                
                speed_file.close()
                dir_file.close()
                    
            
        dataset.close()
            




def read_loc_file(fname, dtype):
    """Reads a locations file and returns name, location ids, latitudes and longitudes"""
    rec = np.genfromtxt(fname, dtype=dtype, delimiter=',')[1:]
    return rec
    
def in_domain(lat, lon, lat2d, lon2d):
    """Tests whether (lat,lon) is within domain defined by lat2d and lon2d.
    Returns boolean, true if the point is within the domain """    

    min_lon = np.min(lon2d)
    max_lon = np.max(lon2d)
    min_lat = np.min(lat2d)
    max_lat = np.max(lat2d)
    
    if (lat < min_lat) or (lat> max_lat) or (lon<min_lon) or (lon>max_lon):
          logger.debug("point (%0.3f, %0.3f) is not within domain (%0.2f, %0.3f, %0.3f, %0.3f)" %(lat, lon, min_lat, max_lat, min_lon, max_lon))
          return False
    else:
        return True


def get_index(lat, lon, lat2d, lon2d):
    """ Finds the nearest mass point grid index to the point (lon, lat).
        Works but is slow as just naively searches through the arrays point
        by point. 
        
        Arguments:
            @lat: the latitude of the target point
            @lon: longitude of the target point
            @lat2d: 2d array of latitudes of grid points
            @lon2d: 2d array of longitudes of grid points
            
       Returns (i,j) of nearest grid cell. Raises exception if outside"""

    logger = wrftools.get_logger()
    logger.debug("finding index of (%0.3f, %0.3f) " %(lat,lon))
    west_east   = lat2d.shape[0]
    south_north = lat2d.shape[1]    
    logger.debug("dimensions of domain are: %d south_north, %d west_east" %(south_north, west_east))
    
    if not in_domain(lat, lon, lat2d, lon2d):
        raise DomainError('point (%0.3f, %0.3f) not in model domain' %(lat, lon))
    
        
    # 
    # slow, but will work. Just search through the arrays until we 
    # hit the nearest grid point
    #
    min_dist = 10000000  # if the point is further than 10M m away, don't bother!
    min_x = 0
    min_y = 0 
    

    for x in range(west_east-1):
        for y in range(south_north-1):            
            point_lat = lat2d[x,y]
            point_lon = lon2d[x,y]
            
            d = tools.haversine(lat, lon, point_lat, point_lon)
            
            if d < min_dist:
                min_dist = d
                min_x = x
                min_y = y
    
    if min_x==0 or min_y==0 or min_x>west_east or min_y>south_north:
        logger.error("Point is on/off edge of of model domain, this should have been caught earlier!")
        raise DomainError("Point is on/off edge of of model domain")
        
   
    logger.debug('nearest grid index is x=%d, y=%d, %0.3f m away' %(min_x, min_y, min_dist))
    logger.debug('latitude, longitude of original is (%0.3f, %0.3f)' %(lat, lon))
    logger.debug('latitude, longitude of index is (%0.3f, %0.3f)' %(lat2d[min_x,min_y], lon2d[min_x,min_y]))
    
    return (min_x, min_y, min_dist)


    
if __name__ == '__main__':
    main()
