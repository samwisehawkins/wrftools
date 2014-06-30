""" 
Module wrftools
=====

Provides a selection of functions for pre-processing and
running a WRF forecast.  

Author: Sam Hawkins sam.hawkins@vattenfall.com

Assumed domains directory structure:

    /working_dir --> namelist.input file and other settings specific to that run
        /wrfout      --> netcdf output from WRF
        /tseries     --> time series extracted at points
        /plots       --> graphical output from NCL


A locations file controls which variables get written to out to time series
This should have the format:
# comments
location_id,name,lat,lon
LOC1, Location One,58.0,1.5
LOC2, Location Two,56.0,-2.5

Time series output files will be named according to:
domain/model_run/tseries/U_80_2006-11-30_00.csv 

TODO
* Change time series ncl code to write netcdf files -- done
* Change namelist reading code to strip trailing commas and remove trailing quotes -- done
* Summarise file transfers in logging output -- done

CHANGES

2014-01-17 Added support for OpenLayers output

2013-08-30 Modified ungrib to support multiple  grib files in one run

2013-07-11 Added job scheduling/queing functionality

2013-06-19 Updated code to allow WRF to be run from any directory. Executables 
           and other required files will be linked in.

2013-02-04 Rationalised the movement to and from /longbackup, now uses rsync for
            flexibility

2012-12-10 Implemented a more aggressive cleanup to remove WPS leftover files


2012-09-13 Updated structure to support operational forecasting, using flag 
           operational=.true. get_cases still needs tidying up

2012-09-05 Uses PyNIO as interpolation, as cnvgrib was failing, meaning time-series
           could not be extracted.

2012-07-27 Added functionality for writing out time series, reading time series
           reading power curves, and converting wind speeds into powers

2012-07-19 Changed shell calls to use run_cmd in order to have enable dummy runs
           where commands are not executed.

2012-05-*  Updated point stat to make much more use of metadata in the output
           in order to facillitate better breakdown of stats when read into database

2012-03-30 Updated run_point_stat to write a more descriptive tag into the 
           'MODEL' field for use in statistical analysis

2012-03-05 Updated functions to operate on one domain only, reading value
           from config[dom], and putting looping structure outside. """



import numpy as np

from dispatch import dispatch
from shared import *

from visualisation import *
from customexceptions import *


from tseries import extract_tseries
from ncdump import ncdump
from power import power, PowerCurve
from queue import fill_template, qsub, qstat




   











