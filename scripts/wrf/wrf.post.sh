#!/bin/bash

. /etc/profile.d/modules.sh

# Module stuff
module load netcdf
module load szip
module load sge
module load openmpi
module add nco

#
# Active comments for SGE 
#
#$ -S /bin/bash
#$ -N wrf.post
#$ -v MPI_HOME
#$ -v LD_LIBRARY_PATH
#$ -cwd
#$ -q all.q
#$ -pe ompi 1
#$ -j yes

#*****************************************************************************
#
# Post-process WRF output files
#
# This script expects to be run as an array job;
# SGE_TASK_ID is used to index into WRF output files
#
# This script performs the following:
#
# 1. Compresses files using nccopy 
# 2. Adds additional attributes 
# 3. Removes the trailing :00:00 and adds .nc
#
#*****************************************************************************

comp_level=9
files=(wrfout*)
index=$(($SGE_TASK_ID - 1))                       # bash arrays are zero-indexed, array jobs start at 1
wrf_file=${files[$index]}
tmp_file=${wrf_file/wrfout/temp_wrfout}

echo "************************************************************"
echo "wrf.post.sh"
echo "post processing ${wrf_file} --> ${tmp_file} --> ${wrf_file}"


# get creation time of namelist.output as time simulation started
token=$(ls -l namelist.output | cut -d" " -f 6-8)
tstart=$(date --date="$token" "+%Y-%m-%d_%H:%M:%S")

# get time now (roughly the time the simulation finished)
tcomplete=$(date +%Y-%m-%d_%M:%H:%S)

# compress files check for attribute first
# 0 if found, 1 if not
compressed=$(ncdump -h ${wrf_file} | grep -c "COMP_LEVEL")
echo $compressed

if [ "$compressed" = "0" ] ; then
    
    CMD="nccopy -k4 -d ${comp_level} ${wrf_file} ${tmp_file}"
    echo $CMD
    $CMD

    if [ ! -s ${tmp_file} ]; then
        echo "error compressing output files"
        exit 1
    fi

    CMD="ncatted -O -h -a COMP_LEVEL,global,c,c,$comp_level ${tmp_file}"
    echo $CMD
    $CMD

    CMD="mv ${tmp_file} ${wrf_file}"
    echo $CMD
    $CMD

else
    echo "file already compressed"
fi

# this adds attributes to the wrfoutput files. Make sure that by the time the script is run, 
# atributes has been replaced by proper attribute definitions, i.e. by defining them in init.yaml
CMD="ncatted -O -h -a MODEL_RUN,global,c,c,"/project/slha/forecasting/highres" -a BOUNDARY_CONDITIONS,global,c,c,"GFS" \
-a WALLCLOCK_START,global,c,c,"$tstart" \
-a WALLCLOCK_END,global,c,c,"$tcomplete" ${wrf_file}"

echo $CMD
$CMD

# finally rename output file if necessary
final_name=${wrf_file/\:00\:00/.nc} 
echo $wrf_file
echo $final_name

if [  "$final_name" != "$wrf_file" ]; then
    CMD="mv $wrf_file $final_name"
    echo $CMD
    $CMD
fi

echo "wrf.post.sh done"
echo "************************************************************"

