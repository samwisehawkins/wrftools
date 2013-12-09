#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      slha
#
# Created:     15/08/2012
# Copyright:   (c) slha 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python


import numpy as np
from math import sqrt, sin, cos, atan2,radians


def index(all, sub):
    """Returns a list of indicies of sub in all """

    l = [all.index(s) for s in sub]
    return l


def circavg(xs, axis):
     avgx = np.ma.mean(np.cos(np.radians(xs)), axis=axis)
     avgy = np.ma.mean(np.sin(np.radians(xs)), axis=axis)
     theta = np.degrees(np.arctan2(avgy, avgx))
     result = np.where(theta<0, theta+360, theta)
     return result


def runs_of_ones_array(bits):
  # make sure all runs of ones are well-bounded
  bounded = np.hstack(([0], bits, [0]))
  # get 1 at run starts and -1 at run ends
  difs = np.diff(bounded)
  run_starts, = np.where(difs > 0)
  run_ends,   = np.where(difs < 0)
  run_lengths = run_ends - run_starts
  idx = np.argmax(run_lengths)
  return idx, run_lengths, run_starts, run_ends


 
  
def filter(data, all_tbs, sel_tbs, lower, upper, method='all'):
    """Returns row indices to filter data where conditions hold.
    This could arguably be done with rec_arrays, but subsetting
    is much more consistent working with ndarrays.

    Warning: using 'median' as a selection method is very memory intensive
    and can lead to out of memory errors.

    Arguments:
        data    -- 2D array to be filtered
        all_tbs -- columns headings of data
        sel_tbs -- headings of columns to apply filtering condition
        lower   -- lower bound for filter
        upper   -- upper bound for filter
        method  -- all:    condition must hold across all cols in sel_tbs
                   median: condition must hold for median across sel_tbs
                   mean:   condition must hold for mean value in sel_tbs
                   circmean: condition must hold for cicrular mean in sel_tbs

   Returns: A set of row indices where condition holds for the specified columns"""

    #
    # Use a subset of columns for filtering
    #
    col_ind    = [all_tbs.index(tbid) for tbid in sel_tbs]
    col_subset = data[:, col_ind]

    if method == 'all':
        row_ind = np.ma.all((col_subset >=lower) & (col_subset<=upper), axis=1)

    if method =='median':
        mids    =  np.ma.median(col_subset, axis=1)
        row_ind = (mids >=lower) & (mids <=upper)

    if method =='mean':
        mids    =  np.ma.mean(col_subset, axis=1)
        row_ind = (mids >=lower) & (mids <=upper)

    if method =='circmean':
        mids    =  circavg(col_subset, axis=1)
        row_ind = (mids >=lower) & (mids <=upper)

    return row_ind






def power_curve(ax, speed, power, scatter=True, bars=False, label=None, annotation=None):
    """ Plot a scatter of power against speed
    Label points with an optional list of of turbine IDs """
    #ax.set_ylim(ymin=0)
    #ax.set_xlim(xmin=0)

    bin_centres = np.arange(math.floor(np.min(speed)), math.ceil(np.max(speed)), 1)
    bin_width   = 1

    #
    # One dimensional data
    #
    if len(power.shape)==1:
        if scatter:
            ax.scatter(speed, power, marker='+', markersize=0.5, label=label)
        if bars:
            bin_means, bin_stds =  moving_bin_avg(speed, power,  bin_centres, bin_width)
            ax.errorbar(bin_centres, bin_means, yerr=bin_stds, fmt='s-')

    #
    # Two dimensional data
    #
    else:
        for n in range(power.shape[1]):
            #
            # One dimensional speed
            #
            if len(speed.shape)==1:
                print '1d speed'
                if scatter:
                    ax.scatter(speed, power[:,n], marker='+', s=1 )
                if bars:
                    bin_means, bin_stds =  moving_bin_avg(speed, power[:,n],  bin_centres, bin_width)
                    #ax.errorbar(bin_centres, bin_means, yerr=bin_stds, fmt='s-', color=[colors[n]][0], label=label[n])
                    ax.errorbar(bin_centres, bin_means, yerr=bin_stds, fmt='s-', label=label[n])

            else:
                if scatter:
                    #ax.scatter(speed[:,n], power[:,n], marker='+', s=1, c=colors[n], edgecolor=colors[n] )
                    ax.scatter(speed[:,n], power[:,n], marker='+', s=1 )
                if bars:
                    bin_means, bin_stds =  moving_bin_avg(speed[:,n], power[:,n],  bin_centres, bin_width)
                    #ax.errorbar(bin_centres, bin_means, yerr=bin_stds, fmt='s-', color=[colors[n]][0], label=label[n])
                    ax.errorbar(bin_centres, bin_means, yerr=bin_stds, fmt='s-', label=label[n])

    if annotation!=None:
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        # place a text box in upper left in axes coords
        ax.text(0.05, 0.95, annotation, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)

    ax.set_xlim(xmin=0, xmax=25)
    ax.set_ylim(ymin=0, ymax=3500)
    ax.set_xlabel('wind speed [m/s]')
    ax.set_ylabel('power [kW]')



def power_curve_bins(speed, power, bin_edges):
    """ Plot bin-averaged power curve with error bars denoting confidence intervals """
    xs, ys, std = bin_average(speed, power, bin_edges)

    fig = plt.figure()
    ax  = fig.add_subplot(111)
    #ax.scatter(xs, ys)
    ax.errorbar(xs, ys, yerr=std, fmt='o')

    plt.xlabel('Wind speed [m/s]')
    plt.ylabel('Power/turbine [kw]')
    plt.show()


def moving_bin_avg(xdata, ydata, bin_centres, bin_width, mask_empty=False):
    """ Produces overlapping bin averages of ydata binned
    according to xdata """

    #
    # Do this as loop to start, can make more pythonic
    # later if needs be
    #
    bin_means = np.ma.zeros(bin_centres.shape)
    bin_stds  = np.ma.zeros(bin_centres.shape)
    bin_counts = np.ma.zeros(bin_centres.shape)

    for n in range(len(bin_centres)):
        ind = (xdata>=bin_centres[n] - bin_width/2.0) \
            & (xdata < bin_centres[n] + bin_width/2.0)

        bin_means[n] = np.mean(ydata[ind])
        bin_stds[n]  = np.std(ydata[ind])
        bin_counts[n]

    if mask_empty:
        bin_means.mask = np.isnan(bin_means)

    return bin_centres, bin_means, bin_stds


def bin_average(xdata, ydata, bin_edges, mask_empty=False):
    """Compute bin-averaged ydata, binned according to xdata
    and bin_edges.

    Returns (bin_centres, bin_means, bin_stds) tuple

    Note, if the bins are defined in such a way that no data points
    fall into some bins, then the bin-average will be a nan, since
    the mean involves a divide by zero.
    The default is to leave this as a nan, the alternative is to
    mask these, use mask_empty=True."""

    bin_centres = 0.5*(bin_edges[0:-1] + bin_edges[1:])

    #
    # Note
    # digitize ignores the mask
    # so any nan values will go into the highest bin, since
    # they are treat like infinity
    # so we need to reconstrunct the mask afterwards
    #
    bin_numbers      = np.ma.array(np.digitize(xdata, bins=bin_edges))
    bin_numbers.mask = xdata.mask

    bin_means   = np.ma.array([np.ma.mean(ydata[bin_numbers==i]) for i in range(1,len(bin_edges))])
    bin_counts  = np.array([np.ma.sum(bin_numbers==i) for i in range(1,len(bin_edges))])
    bin_stds    = np.ma.array([np.ma.std(ydata[bin_numbers==i]) for i in range(1,len(bin_edges))])

    if mask_empty:
        bin_means.mask = (bin_counts==0)
        bin_stds.mask  = (bin_counts==0)


    return bin_centres, bin_means, bin_stds



def bearing(u, v):
    """ Simplified formulation of above """
    
           
    #this is the anticlockwise angle from the x axis to the vector 
    degrees = np.degrees(np.arctan2(v,u))
    
    # this is clockwise angle from the y axis to the vector
    yangle = 90 - degrees

    np.where(yangle < 0, yangle+360, yangle)
    b = (yangle - 180) % 360
    return b

def bearing_between(lat1, lon1, lat2, lon2):
    dlon = radians(lon2-lon1)
    lat1rad = radians(lat1)
    lon1rad = radians(lon1)
    lat2rad = radians(lat2)
    lon2rad = radians(lon2)

    theta = degrees(atan2(sin(dlon)*cos(lat2rad), cos(lat1rad)*sin(lat2rad) - sin(lat1rad)*cos(lat2rad)*cos(dlon)))
    if theta<0: theta = theta + 360
    return theta


def haversine(lat1, lon1, lat2, lon2):

    #
    # From http://www.movable-type.co.uk/scripts/latlong.html
    #
    lat1rad = radians(lat1)
    lon1rad = radians(lon1)
    lat2rad = radians(lat2)
    lon2rad = radians(lon2)

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    R    = 6371000
    a = sin(dlat/2.0)**2 + cos(lat1rad)*cos(lat2rad)*(sin(dlon/2.0)**2)
    c = 2*atan2(sqrt(a), sqrt(1-a))
    d = R*c
    return d


