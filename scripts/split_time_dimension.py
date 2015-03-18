"""Splits the time dimension into an reftime and a leadtime 
so that multiple files can be concatenated more easily"""
import sys
from netCDF4 import Dataset, num2date, date2num

for f in sys.argv[1:]:
    dataset = Dataset(f, 'a')

    # rename record dimension to reftime
    dataset.renameDimension('record', 'reftime')
    
    # rename time dimension to leadtime
    dataset.renameDimension('time', 'leadtime')    
    
    dataset.renameVariable('time', 'leadtime')
    time = dataset.variables['leadtime']

    reftime = dataset.createVariable('reftime', 'f8', ('reftime',))
    reftime.units = time.units
    reftime.calendar = time.calendar
    reftime[0] = time[0]
    reftime.standard_name = "forecast_reference_time"
    reftime.long_name = "Time of model initialization" 

    
    dt = num2date(time[:], units=time.units, calendar=time.calendar)
    lt = date2num(dt, units="hours since %s" % dt[0], calendar=time.calendar)

    # use the existing time variable to hold lead time information
    
    time.units = "hours"
    time.standard_name = "forecast_period"
    time.long_name = "hours since forecast_reference_time"
    time[:] = lt
    del(time.calendar)
    
    dataset.renameVariable('location', 'old_location')
    dataset.renameVariable('lat', 'old_lat')
    dataset.renameVariable('lon', 'old_lon')
    dataset.renameVariable('height', 'old_height')
        
    loc = dataset.createVariable('location', 'S1', ('location','loc_str_length'))
    lat = dataset.createVariable('lat', 'f8', ('location',))
    lon = dataset.createVariable('lon', 'f8', ('location',))
    hgt = dataset.createVariable('height','i4',('height',))
    
    loc[:] = dataset.variables['old_location'][0]
    lat[:] = dataset.variables['old_lat'][0]
    lon[:] = dataset.variables['old_lon'][0]
    hgt[:] = dataset.variables['old_height'][0]
    
    
    dataset.close()



