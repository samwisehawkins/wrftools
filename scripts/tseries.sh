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
#$ -N tseries
#$ -v MPI_HOME
#$ -v LD_LIBRARY_PATH
#$ -cwd
#$ -q all.q
#$ -pe ompi 1
#$ -j yes


# This script expects to be run as an array job, so that SGE_TASK_ID corresponds to the file to operate on

files=(wrf/wrfout*)
index=$(($SGE_TASK_ID - 1))                       # bash arrays are zero-indexed, array jobs start at 1
ncl_in_file=${files[$index]}

name=${ncl_in_file##*/}
new_name=${name/wrfout/tseries}

ncl_out_file="tseries/${new_name}"


echo $ncl_in_file
echo $ncl_out_file

NCL_WRFTOOLS="ncl/wrftools.ncl  NCL_IN_FILE=${ncl_in_file} NCL_OUT_FILE=${ncl_out_file} NCL_LOC_FILE=locations.csv NCL_OUT_TYPE=nc NCL_OPT_FILE=options.ncl ncl ncl/extract_time_series.ncl


