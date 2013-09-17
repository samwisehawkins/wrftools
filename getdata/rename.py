import os 
import sys

fnames = sys.argv[1:]
for f in fnames:
    path, name = os.path.split(f)
    if path=='':
        path='.'
    tokens = name.split('.')
    new_name = '%s/%s.%s.grb2' %(path,tokens[0], tokens[1])
    print new_name
    os.rename(f, new_name)