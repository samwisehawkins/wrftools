""" power.py creates power output from wind speed and direction times series 

Usage:
    power.py [--config=<file>]
        [--log_level=<level>]
        
Options:
    [--log_level=<level>]"""



import numpy as np
import os
import scipy
from scipy import interpolate
#import wrftools
import loghelper as log
import sys
import confighelper as conf

LOGGER="power"

def main():
    config = conf.config(__doc__, sys.argv[1:], flatten=True)
    print config
    power(config)

def power(config):
    """Reads 'time series' from netcdf time series file, and adds power as a variable. """
    
    from netCDF4 import Dataset
    from netCDF4 import netcdftime
    
    #
    # How to output power? We could output to a simple CSV format.
    # We could output to a netcdf file, by for example adding power
    # as a variable in the netcdf file. Or we could go directly to json format. 
    # Advantage of going to netCDF is we can dump the resulting file to JSON format
    # once. Advantage of going straight to JSON is that it is simpler.  
    # In fact, I could recreate the old technique of writing individual files,
    # one per series. Could make some json tools. One to cat series together,
    # which would be remove 
    #
    # series to JSON files, e.g. 
    #{ wind_10
    # model_run  = 'test',
    # grid_id    = 3,
    # time_units = 'milliseconds since 1900'
    # data = {timestamp, }
    #}

    logger          = log.create(LOGGER, config['log_level'], config['log_fmt'], config['log_file'])
    

    #domain          = config['domain']
    #domain_dir      = config['domain_dir']
    #model           = config['model']
    #model_run       = config['model_run']
    
    # Number of samples to use should be in here
    # Whether to normalise power should be in here    
    pnorm           = config['pnorm']
    pdist           = config['pdist']
    sstd            = config['sstd']
    dstd            = config['dstd']
    pquants         = config['pquants']
    quantiles       = np.array(pquants)
    
    logger.debug(quantiles)
    
    if pdist:
        n=pdist
            
    dom             = config['dom']
    init_time       = config['init_time']
    locations_file  = config['locations_file']
    pcurve_dir      = config['pcurve_dir']
    ts_dir          = config['tseries_dir']
    tseries_file    = '%s/tseries_d%02d_%s.nc' % (ts_dir, dom, init_time.strftime('%Y-%m-%d_%H'))
    
    logger.info('*** Estimating power from time series: %s ' % tseries_file)
    dataset = Dataset(tseries_file, 'a')

    # Get dimensions
    dims    = dataset.dimensions
    ntime   = len(dims['time'])
    nloc    = len(dims['location'])
    nheight = len(dims['height'])
    
    # Get coordinate variables
    nctime    = dataset.variables['time']
    datetimes = netcdftime.num2date(nctime, nctime.units)
    location = [''.join(l.filled(' ')).strip() for l in dataset.variables['location']]
    height   = dataset.variables['height']

    # Get attributes
    domain = dataset.getncattr('DOMAIN')
    domain = dataset.getncattr('MODEL_RUN')
    model  = dataset.getncattr('MODEL')

    # Get number of quantiles
    nq    = len(quantiles)
    pdata = np.ma.zeros((ntime,nloc,nheight,nq+1), np.float) # mean will be 1st value
   
    for l,loc in enumerate(location):
        logger.info('Predicting power output for %s' % loc )
        pcurve_file = '%s/%s.csv' %(pcurve_dir, loc)
        
        # mask power data if no power curve found for this park
        if not os.path.exists(pcurve_file):
            logger.debug("Power curve: %s not found, skipping" % pcurve_file)
            pdata[:,l,:,:] = np.ma.masked
            continue

        #
        # Open power curve
        #
        pcurve = from_file(pcurve_file)

        # we could eliminate this loop by applying 
        # pcurve to all the speed, direction values over all heights
        # and reshaping the arrays. DO THAT! 
        for h in range(nheight):
            speed     = dataset.variables['SPEED'][:,l,h]
            direction = dataset.variables['DIRECTION'][:,l,h]
            
            #pwr = pcurve.power(speed,direction)
    
            # pdist will create a distribution for each timetep based on sampling
            # n times from a normal distribution. 
            pdist   = pcurve.power_dist(speed, direction, sstd=sstd,dstd=dstd,n=n, normalise=pnorm)
            pmean   = np.mean(pdist, axis=1)
            pquants = scipy.stats.mstats.mquantiles(pdist, prob=quantiles/100.0,axis=1, alphap=0.5, betap=0.5)
            
            print 'raw quantile values from mquantiles'
            pdata[:,l,h,0]  = pmean
            pdata[:,l,h,1:] = pquants[:,:]

        logger.info('finished %s' % loc)            

    # UTH is location 7
    #print pdata[:,7,0,0]  # should be mean
    #print pdata[:,7,0,1]  # P10
    #print pdata[:,7,0,2]  # P90  
    
    pavg    = dataset.createVariable('POWER','f',('time','location','height'))
    pavg.units = 'kW'
    pavg.description = 'forecast power output'
    pavg[:] = pdata[:,:,:,0]

    
    for q, qval in enumerate(quantiles):

        varname = 'POWER.Q%02d' % qval
        logger.debug("creating variable %s" % varname)
        var  = dataset.createVariable(varname,'f',('time','location','height'))
        if pnorm:
            var.units = 'ratio'
        else:
            var.units = 'kW'
        var.description = 'forecast power output'
        print pdata[:,:,:,q+1]
        var[:] = pdata[:,:,:,q+1]
    
            

    
    dataset.close()

class PowerCurve(object):
    """Represents a power curve, provides power(speed, direction) method to convert
    wind speed and direction into power """

    def __init__(self, scentres, dcentres, pcentres):
        """
        Creates a PowerCurve with a RectBivariateSpline to linearly interpolate power
        from speed and direction

        Arguments:
            scentres -- centre of speed bins
            dcentres -- direction bin centres
            pcentres -- array of shape[size(scentres), size(dcentres)] giving power by speed and direction"""

        if pcentres.shape != (scentres.shape[0], dcentres.shape[0]):
            raise Exception('power should be of size [scentres.shape[0], dcentres.shape[0]]')

        self._scentres = scentres
        self._dcentres = dcentres
        self._pcentres = pcentres
        self._spline   = interpolate.RectBivariateSpline(scentres, dcentres, pcentres, kx=1, ky=1, s=0)

    def power(self, speed, direction, normalise=False):
        """Returns an array of power interpolated from the speed and direction pairs.
        Due to the implemtation of the RectBivariateSpline, which requires that the data
        is monotonic increasing, this must loop through values and do them pairwise """
        
        assert speed.shape==direction.shape
        
        result = np.array([self._spline(s,v) for (s,v) in zip(speed.flatten(), direction.flatten())])

        if normalise:
            result = result/float(np.max(self._pcentres))
       
        return result.reshape(speed.shape)
        

    def power_dist(self, speed, direction, sstd=None, dstd=None, n=None, normalise=False):
        """Returns an array of power interpolated from the speed and direction pairs,
        with independent normal distribution applied to the speed and direction.
        Due to the implemtation of the RectBivariateSpline, which requires that the data
        is monotonic increasing, this must loop through values and do them pairwise 
        
            Arguments:
                speed: 1d array of wind speed values
                sstd:  1d array of wind direction values
                dstd:  standard deviation to apply to wind speed values when sampling from Normal distribution
                dddev: standard deviation to wind direction values when sampling from Normal distribution
                n:     number of sample points to use when drawing from distributions
            
            Returns:
                ndarray with first dimension the same as speed and direction, and second dimension of size n if specified"""
        
        from scipy.stats import norm
        assert speed.shape==direction.shape
        
        # generate a randomly sampled speed distribution
        sdist = np.array([norm(loc=s, scale=sstd).rvs(n) for s in speed])
        ddist = np.array([norm(loc=d, scale=dstd).rvs(n) for d in direction])
        
        pdist = np.array([self._spline(s,d) for (s,d) in zip(sdist.flatten(), ddist.flatten())])
        
        if normalise:
            pdist = pdist/float(np.max(self._pcentres))
        
        return pdist.reshape(speed.shape[0], n)
        
        
        
    def tofile(self, filename):
        """ Write a textual repesenation of PowerCurve"""
        f = open(filename, 'w')

        #
        # TODO
        # Only write basics for now, add any headers later
        # Which orientation to we write to?
        #
        # pcentres(speed, direction)
        #
        f.write('0.0,')
        drow = ','.join(map(str, self._scentres))
        f.write(drow)
        f.write('\n')
        for j in range(self._dcentres.shape[0]):
            f.write('%s,' % self._dcentres[j])
            row = ','.join(map(str, self._pcentres[:, j]))
            f.write(row)
            f.write('\n')
        f.close()


def from_file(filename):

    data = np.loadtxt(filename, delimiter=',')

    scentres = data[0, 1:]
    dcentres = data[1:, 0]
    pcentres = data[1:, 1:].T

    pcurve = PowerCurve(scentres, dcentres, pcentres)
    return pcurve


##    f = open(filename, 'r')
##    tokens   = [l.split(',') for l in f.read().split('\n')]
##    data     = map(float, )
##    scentres = map(float, tokens[0][1:])
##    print scentres




def example_interpolation():

    # Note that the output interpolated coords will be the same dtype as your input
    # data.  If we have an array of ints, and we want floating point precision in
    # the output interpolated points, we need to cast the array as floats
    data = np.arange(40).reshape((8,5)).astype(np.float)

    # I'm writing these as row, column pairs for clarity...
    coords = np.array([[1.2, 3.5], [6.7, 2.5], [7.9, 3.5], [3.5, 3.5]])
    # However, map_coordinates expects the transpose of this
    coords = coords.T

    # The "mode" kwarg here just controls how the boundaries are treated
    # mode='nearest' is _not_ nearest neighbor interpolation, it just uses the
    # value of the nearest cell if the point lies outside the grid.  The default is
    # to treat the values outside the grid as zero, which can cause some edge
    # effects if you're interpolating points near the edge
    # The "order" kwarg controls the order of the splines used. The default is
    # cubic splines, order=3
    zi = ndimage.map_coordinates(data, coords, order=3, mode='nearest')

    row, column = coords
    nrows, ncols = data.shape
    im = plt.imshow(data, interpolation='nearest', extent=[0, ncols, nrows, 0])
    plt.colorbar(im)
    plt.scatter(column, row, c=zi, vmin=data.min(), vmax=data.max())
    for r, c, z in zip(row, column, zi):
        plt.annotate('%0.3f' % z, (c,r), xytext=(-10,10), textcoords='offset points',
                arrowprops=dict(arrowstyle='->'), ha='right')
    plt.show()




#if __name__ == '__main__':
#    main()






    
def test():

##    example_interpolation()
##    plt.close()

    dcentres = np.arange(0, 360, 10)
    print 'directions',  dcentres.shape

    scentres = np.arange(1,30.5, 1)
    print 'speeds',  scentres.shape

    psingle = np.arange(100, 3000.5, 100)
    print 'power single', psingle.shape

    fig = plt.figure()
    ax = fig.gca(projection='3d')

    xs = scentres
    ys = dcentres
    zs = np.zeros((xs.shape[0], ys.shape[0]), 'f' ) + psingle[:, np.newaxis]

    X, Y = np.meshgrid(xs, ys)
    Z    = zs.T

    print 'xs', xs.shape
    print 'ys', ys.shape
    print 'zs', zs.shape


    print 'X', X.shape
    print 'Y', Y.shape
    print 'Z', Z.shape

    ax.plot_wireframe(X, Y, Z)

    pcurve = PowerCurve(xs, ys, zs)
    spoints = [1,   5,  10,  20,  25]
    dpoints = [70, 180, 275, 350, 500]


    xpoints = spoints
    ypoints = dpoints
    zpoints = pcurve.power(xpoints, ypoints)[:, 0]

    print xpoints
    print ypoints
    print zpoints
    print zpoints.shape
    #ax.scatter(xpoints, ypoints, zpoints)

    pcurve.tofile(r'C:\UnBackedUp_Data\pcurve.csv')
    pcurve2 = fromfile(r'C:\UnBackedUp_Data\pcurve.csv')
    zpoints2 = pcurve2.power(xpoints, ypoints)[:,0]
    ax.scatter(xpoints, ypoints, zpoints2, 's')
    plt.show()

if __name__ == "__main__":
    main()