#!/usr/bin/python2.7
import datetime
from dateutil import rrule
import subprocess
from math import *

var_list = ['SLP','U850','U500','V850','V500','T850','T500','T250','Q850','Q500','H1000','H850','H500','OMEGA500',
            'U10M','U2M','U50M','V10M','V2M','V50M','T10M','T2M','QV10M','QV2M','TS','DISPH','XDim','YDim','TIME','XDim_EOS','YDim_EOS','Time']


min_lon = -30
max_lon = 30
min_lat = 40
max_lat = 75


start = datetime.datetime(2012, 6, 6, 0)
end   = datetime.datetime(2012, 6, 7, 0)
rrule = rrule.rrule(rrule.DAILY, dtstart=start, until=end)

server     = 'http://goldsmr2.sci.gsfc.nasa.gov/opendap/MERRA/MAT1NXSLV.5.2.0'
local_dir  = '$HOME/forecasting/data/reanalysis/MERRA' 
version    = 0            

# determine stream by start date
if start.year<1989:
    stream = 1
elif start.year<1988:
    stream = 2
else:
    stream=3

stream_spec = 'MERRA%d%02d' %(stream, version)    
collection = '%s.prod.assim.tavg1_2d_slv_Nx' % stream_spec


#
# MERRA is on 2/3 degree  by 1/2 degree
# dimensions 540 by 361. So a quick and dirty
# caluclation can be done to work out left and right 
# limits         
xmin = int(floor((min_lon+180)*540/360.0))
xmax = int(ceil((max_lon+180)*540/360.0))
ymin = int(floor((min_lat+90)*360/180.0))
ymax = int(ceil((max_lat+90)*360/180.0))

dim_spec = '-d XDim,%s,%s -d YDim,%s,%s' % (xmin, xmax, ymin,ymax)
var_spec = '-v %s' % ','.join(var_list)



print '\n\n*****************************************'
print 'Fetching MERRA data using ncks via OpenDAP'
print 'Server: ', server
print 'Start: ', start
print 'End: ', end
print 'Bounding box:', min_lat, max_lat, min_lon, max_lon
print 'Dim spec', dim_spec
print 'Var spec', var_spec
print 'Stream and version', stream_spec
print 'Local dir: ', local_dir


for d in rrule:
    date_str = d.strftime('%Y%m%d')
    outname = '%s/%s.%s.nc' %(local_dir, collection, date_str)
    tmpname = outname+'.incoming'
    cmd = 'ncks %s %s %s/%d/%02d/%s.%s.hdf %s' %(var_spec, dim_spec,server, d.year,d.month, collection, date_str, tmpname)
    subprocess.call(cmd, shell=True)

    cmd = 'nccopy -d 9 %s %s' % (tmpname, outname)
    subprocess.call(cmd, shell=True)    
    cmd = 'rm %s' % tmpname
    subprocess.call(cmd, shell=True)
print '*****************************************\n\n'
