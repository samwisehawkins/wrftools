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
#$ -N real
#$ -v MPI_HOME
#$ -v LD_LIBRARY_PATH
#$ -cwd
#$ -pe ompi 1
#$ -j yes

ln -sf ../metgrid/met_em* ./

CMD="$MPI_HOME/bin/mpirun real.exe"
 
echo $CMD
 
$CMD

