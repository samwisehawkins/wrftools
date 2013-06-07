#!/usr/bin/env python

USAGE = """python test_namelist namelist """

import sys
from wrftools import wrftools
args = sys.argv[1:]
if len(args)!=2:
    print USAGE
    sys.exit(1)



namelist = wrftools.read_namelist(args[0])
print namelist


