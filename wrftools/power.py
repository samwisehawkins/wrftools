""" power.py creates power output from wind speed and direction times series 

Usage:
    power.py [--config=<file>] [options]

        
Options:
    --log-level=<level>       debug, info or warn
    --init-time=<datetime>    initial time
    --pcurve-dir=<dir>        power curve dir
    """

import os
import sys
import numpy as np
import datetime
import scipy
from scipy import interpolate
import loghelper
import confighelper as conf
import ncframe
import netCDF4
from netCDF4 import Dataset
from netCDF4 import netcdftime
from substitute import expand


LOGGER="power"

class FileInputEror(Exception):
    pass
    
    
def main():
    config = conf.config(__doc__, sys.argv[1:])
    power(config)

def power(config):
    """Reads 'time series' from netcdf time series file, and adds power as a variable. """
    
    if __name__ == "__main__":
        logger = loghelper.create_logger(config)
    else:
        logger = loghelper.get_logger(config['log.name'])
    
    # Number of samples to use should be in here
    # Whether to normalise power should be in here    
    pnorm           = config['pnorm']
    pdist           = config['pdist']
    sstd            = config['sstd']
    dstd            = config['dstd']
    pquants         = config['pquants']
    quantiles       = np.array(pquants)
    
    
    logger.debug(pnorm)
    
    if pdist:
        n=pdist
            
    grid_id         = config['grid_id']
    init_time       = config['init_time']
    pcurve_dir      = config['pcurve_dir']
    ts_dir          = config['tseries_dir']
    
    tseries_file    = expand(config['tseries_file'], config)
    power_file      = expand(config['power_file'], config)

    logger.info('Estimating power from time series: %s ' % tseries_file)
    logger.info('Writing power time series to: %s ' % power_file)
    
    dataset_in = Dataset(tseries_file, 'a')

            
        
    # Get dimensions
    dims      = dataset_in.dimensions
    nreftime  = len(dims['reftime'])
    ntime     = len(dims['leadtime'])
    nloc      = len(dims['location'])
    nheight   = len(dims['height'])
    loc_str_len = len(dims['loc_str_length'])
    
    # Get coordinate variables
    reftime   = dataset_in.variables['reftime']
    leadtime  = dataset_in.variables['leadtime']
    
    refdt     = netcdftime.num2date(reftime[:], reftime.units)
    
    if "hour" in leadtime.units:
        delta = datetime.timedelta(0,60*60)
    
    elif "minute" in leadtime.units:
        delta = datetime.timedelta(0,60)

    else:
        raise FileInputError("leadtime units of %s not supported" % leadtime.units) 
    
    logger.debug(leadtime)
    logger.debug(type(leadtime[:]))
    logger.debug(type(leadtime[:]))
    datetimes = refdt[:] + (leadtime[:] * delta)
    
    logger.debug(datetimes)
    location = [''.join(l.filled(' ')).strip() for l in dataset_in.variables['location']]
    height   = dataset_in.variables['height']

    # Get attributes
    metadata = config['metadata']

    
    if power_file == tseries_file:
        dataset_out = dataset_in
    else:
        dataset_out = Dataset(power_file, 'w')

        
    # Get number of quantiles
    nq    = len(quantiles)
    pdata = np.ma.zeros((ntime,nloc,nheight,nq+1), np.float) # mean will be 1st value
    
    use_locs = []
    for l,loc in enumerate(location):
    
        pcurve_file = '%s/%s.csv' %(pcurve_dir, loc)
        
        # mask power data if no power curve found for this park
        if not os.path.exists(pcurve_file):
            #logger.debug("Power curve: %s not found, skipping" % pcurve_file)
            pdata[:,l,:,:] = np.ma.masked
            continue
        
        logger.info('Predicting power output for %s' % loc )
        #
        # Open power curve
        #
        use_locs.append(l)
        pcurve = from_file(pcurve_file)

    
        for h in range(nheight):
            speed     = dataset_in.variables['SPEED'][0,:,l,h]
            direction = dataset_in.variables['DIRECTION'][0,:,l,h]
            
            #pwr = pcurve.power(speed,direction)
    
            # pdist will create a distribution for each timetep based on sampling
            # n times from a normal distribution. 
            pdist   = pcurve.power_dist(speed, direction, sstd=sstd,dstd=dstd,n=n, normalise=pnorm)
            pmean   = np.mean(pdist, axis=1)
            pquants = scipy.stats.mstats.mquantiles(pdist, prob=quantiles/100.0,axis=1, alphap=0.5, betap=0.5)
            

            pdata[:,l,h,0]  = pmean
            pdata[:,l,h,1:] = pquants[:,:]

        logger.info('finished %s' % loc)            



    use_inds = np.array(use_locs)

    if dataset_out != dataset_in:

        dataset_out.createDimension('reftime', None)
        dataset_out.createVariable('reftime', 'float', ('reftime',))
        dataset_out.variables['reftime'][:] = reftime[:]
        dataset_out.variables['reftime'].units = reftime.units
        dataset_out.variables['reftime'].calendar = reftime.calendar
        dataset_out.variables['reftime'].long_name = reftime.long_name
        dataset_out.variables['reftime'].standard_name = reftime.standard_name

        
        dataset_out.createDimension('leadtime', len(leadtime))
        dataset_out.createVariable('leadtime', 'int', ('leadtime',))
        dataset_out.variables['leadtime'][:] = leadtime[:]
        dataset_out.variables['leadtime'].units = leadtime.units
        dataset_out.variables['leadtime'].long_name = leadtime.long_name
        dataset_out.variables['leadtime'].standard_name = leadtime.standard_name
        
        dataset_out.createDimension('location', len(use_locs))
        dataset_out.createDimension('loc_str_length', loc_str_len)
        
        loc_data =np.array([list(l.ljust(loc_str_len, ' ')) for l in location])
        logger.debug(loc_data)
        dataset_out.createVariable('location', 'c', ('location', 'loc_str_length'))
        dataset_out.variables['location'][:] = loc_data[use_inds,:]
        
        dataset_out.createDimension('height', nheight)        
        dataset_out.createVariable('height', 'i', ('height',))
        dataset_out.variables['height'][:] = height[:]
        dataset_out.GRID_ID = dataset_in.GRID_ID
        dataset_out.DX = dataset_in.DX
        dataset_out.DY = dataset_in.DY
        
        try:
            dataset_out.variables['height'].units = height.units
        except Exception:
            logger.warn("height units missing")
        
        
        pdata = pdata[:, use_inds, :, :]
        for key in metadata.keys():
            key = key.upper()
            logger.debug(key)
            dataset_out.setncattr(key,dataset_in.getncattr(key))
            
        
    
    pavg    = dataset_out.createVariable('POWER','f',('reftime','leadtime','location','height'))
    pavg.units = 'kW'
    pavg.description = 'forecast power output'
    pavg[0,:,:,:] = pdata[:,:,:,0]

    
    for q, qval in enumerate(quantiles):

        varname = 'POWER.P%02d' % qval
        logger.debug("creating variable %s" % varname)
        var  = dataset_out.createVariable(varname,'f',('reftime','leadtime','location','height'))
        if pnorm:
            var.units = 'ratio'
        else:
            var.units = 'kW'
        var.description = 'forecast power output'

        var[0,:,:,:] = pdata[:,:,:,q+1]
    
            

    
    dataset_in.close()
    if dataset_out!=dataset_in:
        dataset_out.close()

    
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
        

    def scale(self, factor):
        self._pcentres = self._pcentres*factor
        
        
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
            print '\n\n\n*********NORMALISING****************'
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