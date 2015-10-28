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
#$ -N <jobname>
#$ -v MPI_HOME
#$ -v LD_LIBRARY_PATH
#$ -cwd
#$ -q all.q
#$ -pe ompi 1
#$ -j yes
#$ -o <logfile>

# This script expects to be run as an array job, so that SGE_TASK_ID corresponds to the nest number
comp_level=9
files=(wrfout*)
index=$(($SGE_TASK_ID - 1))                       # bash arrays are zero-indexed, array jobs start at 1
wrf_file=${files[$index]}
target_file=${wrf_file/\:00\:00/.nc}


echo "post processing ${wrf_file} --> ${target_file}"

# rename the wrfout file slightly - replace minute and seconds and add nc extension

# compress
CMD="nccopy -k4 -d ${comp_level} ${wrf_file} ${target_file}"
$CMD

# this adds attributes to the wrfoutput files. Make sure that by the time the script is run, 
# atributes has been replaced by proper attribute definitions, i.e. by defining them in init.yaml
ncatted -O -h <attributes> ${target_file}
rm ${wrf_file}

