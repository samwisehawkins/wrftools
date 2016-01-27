#!/bin/bash

. /etc/profile.d/modules.sh

# Module stuff
module load netcdf
module load szip
module load sge
module load openmpi

#
# Active comments for SGE 
#
#$ -S /bin/bash
#$ -N power
#$ -v MPI_HOME
#$ -v LD_LIBRARY_PATH
#$ -cwd
#$ -q all.q
#$ -pe ompi 1
#$ -j yes


files=(tseries/tseries*)
index=$(($SGE_TASK_ID - 1))                       # bash arrays are zero-indexed, array jobs start at 1
file=${files[$index]}
out=${file/tseries_/power_}

python $HOME/code/powerup/powerup.py --config=power.yaml --out=$out $file
