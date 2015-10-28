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
#$ -o finalise.log

# Finalise, clean up messy files, do any moving of time-series, plots etc

mv  wrf/wrfout* ../wrfout/
mv  tseries/tseries* ../tseries/
rm metgrid/met_em*
rm metgrid/???\:*

