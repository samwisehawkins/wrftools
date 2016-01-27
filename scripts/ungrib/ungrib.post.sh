#!/bin/bash

. /etc/profile.d/modules.sh

# Module stuff
module load netcdf
module load sge
module load openmpi
module add ncl
module add nco
module switch ncl/opendap ncl/nodap

#
# Active comments for SGE 
#
#$ -S /bin/bash
#$ -N ungrib.post
#$ -v MPI_HOME
#$ -v LD_LIBRARY_PATH
#$ -cwd
#$ -q all.q
#$ -pe ompi 1
#$ -j yes


# assumes that the ungrib output files have a three letter prefix followed by a colon
CMD="mv ???\:* ../metgrid"
echo $CMD
$CMD

 

