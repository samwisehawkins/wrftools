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
#$ -o <logname>

# Script to run NCL visualisations. Expects to be run as an array job with one task per domain.
# This will run ncl with every .ncl file in the directory. 

wrf_file="../wrf/wrfout_${dom}*"
ncl_options="../options.ncl"
ncl_out_dir="../plots"

# check we should have exactly one file
nfiles=`ls -l ${wrf_file} | wc -l`
if [ $nfiles -ne 1 ]
then 
    echo "expected one wrfoutput file"
    exit 1
fi

# modify this if you don't want to run with every single .ncl within the directory
for script in wrf_*.ncl
do
    NCL_IN_FILE=${wrf_file}.nc NCL_OUT_DIR=${ncl_out_dir} NCL_OPT_FILE=${ncl_options} ncl $script
done


