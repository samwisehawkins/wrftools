#!/bin/bash
# initialise a directory for WRF simulations
SCRIPT=$(readlink -f $0)
SCRIPTPATH=`dirname $SCRIPT`

target=$1
cd $target
cp $SCRIPTPATH/config/init.yaml $target
python $SCRIPTPATH/init.py --config=$target/init.yaml
rm $target/init.yaml


