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
#$ -N wrfpost
#$ -v MPI_HOME
#$ -v LD_LIBRARY_PATH
#$ -cwd
#$ -q all.q
#$ -pe ompi 40
#$ -j yes
#$ -o wrf.post.log

comp_level=9
tmp_name="wrfout.tmp"
wrf_file="wrfout_${dom}*"

# check we should have exactly one file
nfiles=`ls -l ${wrf_file} | wc -l`
if [ $nfiles -eq 1 ]
then 
    CMD="nccopy -k4 -d ${comp_level} ${wrf_file} ${tmp_name}"
    echo $CMD
    CMD="mv ${tmp_name} ${wrf_file}"
    echo $CMD
else
    echo "expected one wrfoutput file"
    exit 1
fi


