from netCDF4 import Dataset
from netCDF4 import netcdftime
import time
import datetime
from dateutil import rrule
import sys

start = datetime.datetime(2011, 7, 15, 0)
end   = datetime.datetime(2012, 4, 22, 0)
rule = rrule.rrule(dtstart=start, until=end, freq=rrule.DAILY)
xind = 34
yind=42

#pattern = '/home/slha/forecasting/data/reanalysis/MERRA/MERRA300.prod.assim.tavg1_2d_slv_Nx.%Y%m%d.nc' 

#files = [d.strftime(pattern) for d in rule]
hour = datetime.timedelta(0, 60*60)
dates =list(rule)

#print '#Lat: 55.5'
#print '#Lon: -4.0'


print 'timestamp,SPEED030,SPEED050,SPEED070,SPEED090,DIR030,DIR050,DIR070,DIR090' 
#for d in dates:
for f in sys.argv[1:]:    
    dataset = Dataset(f, 'r')
    #xDim = dataset.variables['XDim'][xind]
    #yDim = dataset.variables['YDim'][yind]
    #h850  = dataset.variables['H850'][:,yind,xind]
    #850  = dataset.variables['U850'][:,yind,xind]
    #v850  = dataset.variables['V850'][:,yind,xind]
    #u50m  = dataset.variables['U50M'][:,yind,xind]
    #v50m  = dataset.variables['V50M'][:,yind,xind]
    #u10m  =  dataset.variables['U10M'][:,yind,xind]
    #v10m  =  dataset.variables['V10M'][:,yind,xind]
    time = dataset.variables['time']
    speed = dataset.variables['SPEED'][:,:,yind, xind]
    direction = dataset.variables['DIRECTION'][:,:,yind, xind]
    dt = netcdftime.num2date(time, time.units)    
    
    for n in range(len(time)):
        t = dt[n].strftime('%Y-%m-%d %H:%M:%S')

        #print '%s,%0.3f,%0.3f,%0.3f,%0.3f,%0.3f,%0.3f,%0.3f' %(t,u10m[n],v10m[n],u50m[n],v50m[n],u850[n],v850[n],h850[n])
        vals = (t,speed[n,1],speed[n,3],speed[n,5],speed[n,7],direction[n,1],direction[n,3],direction[n,5],direction[n,7])
        formats = '%s,' + ','.join(['%0.3f']*(len(vals)-1))
        print formats % vals
        
    dataset.close()