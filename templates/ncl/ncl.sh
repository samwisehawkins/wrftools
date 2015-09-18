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
#$ -N visualise
#$ -v MPI_HOME
#$ -v LD_LIBRARY_PATH
#$ -cwd
#$ -q all.q
#$ -pe ompi 1
#$ -j yes
#$ -o visualise.<job-id>.log

wrf_file="../wrfout_${dom}*"
ncl_options="../options.ncl"


# check we should have exactly one file
nfiles=`ls -l ${wrf_file} | wc -l`
if [ $nfiles -ne 1 ]
then 
    echo "expected one wrfoutput file"
    exit 1
fi

for script in *.ncl
do
    NCL_IN_FILE=${wf_file} NCL_OPT_FILE={ncl_options} ncl $script
done


