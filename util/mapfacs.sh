#!/bin/bash

# Prints out minimum and maximum MAPFAC_M
# from WRF geo_em files to facilitate quick 
# checking of domain suitability

for f in geo_em/geo_em.*
do 
    ncwa -y max -v MAPFAC_M $f max.nc
    ncdump  max.nc | grep "MAPFAC_M = "
    ncwa -y min -v MAPFAC_M $f min.nc
    ncdump  min.nc | grep "MAPFAC_M = "
    rm max.nc
    rm min.nc
done
