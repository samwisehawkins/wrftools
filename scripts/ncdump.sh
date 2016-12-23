#!/bin/bash

. /etc/profile.d/modules.sh

# Module stuff
source activate 3.4
module load netcdf
module load szip
module load sge
module load openmpi

#
# Active comments for SGE 
#
#$ -S /bin/bash
#$ -N ncdump
#$ -v MPI_HOME
#$ -v LD_LIBRARY_PATH
#$ -cwd
#$ -q all.q
#$ -pe ompi 1
#$ -j yes


files=(tseries/tseries*)
index=$(($SGE_TASK_ID - 1))                       # bash arrays are zero-indexed, array jobs start at 1
dom="d0$SGE_TASK_ID"

file=${files[$index]}
python $HOME/code/nctools/ncdump.py --config=config/ncdump_met.yaml --out=json/fcst_data_d01_00Z.json $file

python $HOME/code/wrfextractor/ncflat.py --config=config/flatten_ury.yaml --out=ury_$dom.csv  $file
python $HOME/code/wrfextractor/ncflat.py --config=config/flatten_pyc.yaml --out=pyc_$dom.csv  $file
python $HOME/code/wrfextractor/ncflat.py --config=config/flatten_gsb.yaml --out=gsb_$dom.csv  $file

files=(tseries/power*)
index=$(($SGE_TASK_ID - 1))                       # bash arrays are zero-indexed, array jobs start at 1
file=${files[$index]}
python $HOME/code/nctools/ncdump.py --config=config/ncdump_power.yaml --out=json/power_data_d01_00Z.json $file


