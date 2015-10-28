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

dom=d`printf "%02d" $SGE_TASK_ID`

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

# Script to run NCL visualisations. Expects to be run as an array job with one task per domain.
# This will run ncl with every .ncl file in the directory. 

files=(wrf/wrfout*)
index=$(($SGE_TASK_ID - 1))                       # bash arrays are zero-indexed, array jobs start at 1
ncl_in_file=${files[$index]}
ncl_options="options.ncl"
ncl_out_dir="plots"
ncl_out_type="png"
ncl_loc_file="locations.csv"

if [[ ${ncl_in_file} =~ *.nc ]]; then
    ncl_in_file="${ncl_in_file}.nc"
fi



# modify this if you don't want to run with every single .ncl within the directory
for script in ncl/wrf_*.ncl
do
    echo "running $script on $ncl_in_file"
    NCL_IN_FILE=${ncl_in_file}.nc NCL_OUT_DIR=${ncl_out_dir} NCL_OUT_TYPE=${ncl_out_type} NCL_OPT_FILE=${ncl_options} NCL_LOC_FILE=${ncl_loc_file} ncl $script
done


