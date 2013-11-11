"""rename.py renames files based on their consituent parts

Usage: 
    rename.py  --delim=<d> --fields=<f1,f2,...,fn> [--dry-run] <file>... 
    
Options:
    --delim=<d>            delimiter to split filename on
    --fields=<f1,f2,...fn> fields to use in the output name
    --dry-run              print name changes but don't make changes
    <file>...              list of files to process    
    
Example:
    Original files: 
        2013.cdas1.pgrbf01.grb 
        2013.cdas1.pgrbf02.grb 
        2013.cdas1.pgrbf03.grb 
    
    rename.py --delim=. --fields=0,2,3 *.grb
        2013.cdas1.pgrbf01.grb --> 2013.pgrbf01.grb
        2013.cdas1.pgrbf02.grb --> 2013.pgrbf02.grb 
        2013.cdas1.pgrbf03.grb --> 2013.pgrbf03.grb """
    
import os 
import sys
import docopt

args = docopt.docopt(__doc__, sys.argv[1:])

fnames = args['<file>']
delim  = args['--delim']
fields = map(int, args['--fields'].split(','))
print fields


for f in fnames:
    path, name = os.path.split(f)
    if path=='':
        path='.'
    tokens = name.split(delim)
    new_fields = delim.join([tokens[n] for n in fields])
    new_name = '%s/%s' %(path,new_fields)
    print '%s ----> %s ' %(f.ljust(50, ' '),new_name)
    if not args['--dry-run']:
        os.rename(f, new_name)
