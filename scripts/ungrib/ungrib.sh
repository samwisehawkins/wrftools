#!/bin/bash

. /etc/profile.d/modules.sh

# Module stuff
module load netcdf
module load sge
module load openmpi

#
# Active comments for SGE 
#
#$ -S /bin/bash
#$ -v MPI_HOME
#$ -v LD_LIBRARY_PATH
#$ -j yes

CMD="$MPI_HOME/bin/mpirun ungrib.exe"
echo $CMD
$CMD

CMD="mv ???\:* ../metgrid"
echo $CMD
$CMD


