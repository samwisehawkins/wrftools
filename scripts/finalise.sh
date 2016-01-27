#!/bin/bash

. /etc/profile.d/modules.sh

# Module stuff
module load netcdf
module load szip
module load sge
module load openmpi
module add ncl
module add nco
module switch ncl/opendap ncl/nodap

#
# Active comments for SGE 
#
#$ -S /bin/bash
#$ -N finalise
#$ -v MPI_HOME
#$ -v LD_LIBRARY_PATH
#$ -cwd
#$ -q all.q
#$ -pe ompi 1
#$ -j yes


# Finalise, clean up messy files, do any moving of time-series, plots etc
ls wrf/wrfout*
echo "scp wrf/wrfout* maestrob:/backup/slha/archive/9km/wrfout/"
scp wrf/wrfout* maestrob:/backup/slha/archive/9km/wrfout/
echo "mv  wrf/wrfout* ../wrfout/"
mv  wrf/wrfout* ../wrfout/
cp plots/* ../plots
cp plots/* /project/slha/WWW/forecast/img/00Z/
echo "mv  tseries/tseries* ../tseries/"
mv  tseries/tseries* ../tseries/


rm metgrid/met_em*
rm metgrid/???\:*
rm wrf/met_em*
rm wrf/wrfinput*
rm wrf/wrfbdy*
mv wrf/rsl.error.0000 wrf/rsl.error
rm wrf/rsl.error.*
rm wrf/rsl.out.*
rm *.po*
