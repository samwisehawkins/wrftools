#!/bin/bash

. /etc/profile.d/modules.sh

# Module stuff
module load netcdf
module load szip
module load sge
module load openmpi

#
# Active comments for SGE 
#
#$ -S /bin/bash
#$ -N status
#$ -v MPI_HOME
#$ -v LD_LIBRARY_PATH
#$ -cwd
#$ -q all.q
#$ -pe ompi 1
#$ -j yes

#
# Create a status.json file which summarises start and end time,
# plus a few other attributes
#
out="json/status.json"

#****************************************************************
# Get start time (roughly) from namelist.output creation
#****************************************************************
if [ -s wrf/namelist.output ]; then

    token=$(ls -l wrf/namelist.output | cut -d " " -f 6-8)
    echo $token
    tstart=$(date --date="$token" +"%Y-%m-%d %H:%M:%S")
else
    tstart=""
fi

#***************************************************************
# Get end time (roughly) from creation time of ??? 
#***************************************************************
if [ -s wrf/rsl.error ]; then
    token=$(ls -l wrf/rsl.error | cut -d " " -f 6-8)
    echo $token
    tend=$(date --date="$token" +"%Y-%m-%d %H:%M:%S")
else
    tend=""
fi

echo "{" > $out
echo '    "forecast_started" : "'"$tstart"'",' >> $out
echo '    "forecast_completed"  : "'"$tend"'",' >> $out
echo '    "boundary_conditions"  : "'"GFS"'"' >> $out

echo "}" >> $out
exit


