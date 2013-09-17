from netCDF4 import Dataset
import time
import datetime
from dateutil import rrule


start = datetime.datetime(2011, 7, 15, 0)
end   = datetime.datetime(2012, 4, 22, 0)
rule = rrule.rrule(dtstart=start, until=end, freq=rrule.DAILY)
xind = 39
yind=31

pattern = '/home/slha/forecasting/data/reanalysis/MERRA/MERRA300.prod.assim.tavg1_2d_slv_Nx.%Y%m%d.nc' 

#files = [d.strftime(pattern) for d in rule]
hour = datetime.timedelta(0, 60*60)
dates =list(rule)

print '#Lat: 55.5'
print '#Lon: -4.0'


print 'timestamp,U10,V10,U50,V50,U850,V850,H850' 
for d in dates:
    f = d.strftime(pattern)
    dataset = Dataset(f, 'r')
    xDim = dataset.variables['XDim'][xind]
    yDim = dataset.variables['YDim'][yind]
    h850  = dataset.variables['H850'][:,yind,xind]
    u850  = dataset.variables['U850'][:,yind,xind]
    v850  = dataset.variables['V850'][:,yind,xind]
    u50m  = dataset.variables['U50M'][:,yind,xind]
    v50m  = dataset.variables['V50M'][:,yind,xind]
    u10m  =  dataset.variables['U10M'][:,yind,xind]
    v10m  =  dataset.variables['V10M'][:,yind,xind]
    for n in range(24):
        t = d + hour*n
        print '%s,%0.3f,%0.3f,%0.3f,%0.3f,%0.3f,%0.3f,%0.3f' %(t,u10m[n],v10m[n],u50m[n],v50m[n],u850[n],v850[n],h850[n])

    dataset.close()