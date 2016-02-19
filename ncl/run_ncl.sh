#!/bin/bash

NCL_IN_FILE="$2" NCL_OUT_DIR=. NCL_LOC_FILE=locations.csv NCL_OPT_FILE=options.ncl NCL_OUT_TYPE=png ncl "$1"
