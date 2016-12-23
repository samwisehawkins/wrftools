#!/bin/bash

. /etc/profile.d/modules.sh

# Module stuff
module load sge
module load openmpi

#
# Active comments for SGE 
#
#$ -S /bin/bash
#$ -N dispatch
#$ -v MPI_HOME
#$ -v LD_LIBRARY_PATH
#$ -cwd
#$ -q graphics.q
#$ -pe ompi 1
#$ -j yes


python $HOME/code/wrftools/fetch.py --config=config/fetch.yaml times.txt
