#!/bin/bash

. /etc/profile.d/modules.sh

# Module stuff
module load sge

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

webdir="${HOME}/WWW/forecast"
archive="maestrob:/backup/${USER}/archive/9km"


# Finalise, clean up messy files, do any moving of time-series, plots etc

# Copy to web directory
echo "cp plots/* ${webdir}/img/00Z/"
cp plots/* "${webdir}/img/00Z/"
echo "cp json/* ${webdir}/data"
cp json/* "${webdir}/data"


# Move things outside of date-based folder to top-level
echo "mv  wrf/wrfout* ../wrfout/"
mv  wrf/wrfout* ../wrfout/
echo "mv  tseries/tseries* ../tseries/"
mv  tseries/tseries* ../tseries/
echo "mv  json/json* ../json/"
mv  json/json* ../json/

echo "cp plots/* ../plots"
cp plots/* ../plots

# Archiving
echo "scp wrf/wrfout* ${archive}/wrfout/"
scp wrf/wrfout* "${archive}/wrfout/"

rm metgrid/met_em*
rm metgrid/???\:*
rm wrf/met_em*
rm wrf/wrfinput*
rm wrf/wrfbdy*
mv wrf/rsl.error.0000 wrf/rsl.error
rm wrf/rsl.error.*
rm wrf/rsl.out.*
rm *.po*
