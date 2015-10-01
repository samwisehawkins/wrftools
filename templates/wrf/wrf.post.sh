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
dom=d`printf "%02d" $SGE_TASK_ID`
comp_level=9
tmp_name="wrfout.tmp"
wrf_file="wrfout_${dom}*"

# check we should have exactly one file
nfiles=`ls -l ${wrf_file} | wc -l`
if [ $nfiles -eq 1 ]
then 
    CMD="nccopy -k4 -d ${comp_level} ${wrf_file} ${tmp_name}"
    $CMD
    CMD="mv ${tmp_name} ${wrf_file}"
    $CMD

    # this adds attributes to the wrfoutput files. Make sure that by the time the script is run, 
    # atributes has been replaced by proper attribute definitions, i.e. by defining them in init.yaml
    ncatted -O -h <attributes> ${wrf_file}
else
    echo "expected one wrfoutput file"
    exit 1
fi


