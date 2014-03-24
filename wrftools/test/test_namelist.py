#!/usr/bin/env python

USAGE = """python sync_namelists namelist.wps namelist.input """

import sys
import wrftools
args = sys.argv[1:]
if len(args)!=1:
    print USAGE
    sys.exit(1)


namelist = wrftools.read_namelist(args[0])
print namelist


