#-------------------------------------------------------------------------------
# Name:    powercuvre
# Purpose: Provides a PowerCurve class which can convert wind speed and direction 
#          into power.  Power curves are specified by direction. 
#          Uses 2D linear interpolation  between speed and direction points. 
#
# Author:    sam.hawkins@vattenfall.com
#
# TODO: work out the behaviour of the bivariate spline, the shape of arrays
#       it returns are unusual.
#
#       Remove scipy depdendency? We only use it to do 2D interpolation
#       which we could probably code in numpy only fairly easily
#
#       write some descriptive headers
#       probably something along the lines of a dictionary: self.info
#       write out self.info with # header tags?
#
# Created:     12/07/2012
# Copyright:   (c) slha 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import numpy as np
from scipy import interpolate

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

    def power(self, speed, direction):
        return self._spline(speed, direction)

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




def main():

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
