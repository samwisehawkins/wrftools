"""get_cfsr.py submit request or fetch previous request for CFSR data

Usage: 
    get_cfsr.py auth --email=<email> --passwd=<passwd> --cookie=<cookie> [--verbose]
    get_cfsr.py submit --start=<YYYY-mm-dd HH:MM> --end=<YYYY-mm-dd HH:MM> --dsid=<dsid> --cookie=<cookie> [--dry-run] [--verbose]
    get_cfsr.py fetch <request>... --cookie=<cookie> [--out=<dir>] [--max-num=<max>] [--dry-run] [--verbose]
    get_cfsr.py (-h | --help)
    
Options:
    --email=<email>   email registered for UCAR RDA account
    --passwd=<passwd> password for UCAR RDA account
    --user=<user>     name used for data directory on RDA server (usually surname)
    --cookie=<cookie> location to read/write authentication cookie
    --dsid=<dsid>     UCAR dataset id e.g. 093.0 or 094.0
    --dry-run         verify but don't submit request
    --out=<dir>       local directory to fetch to [default: ./]
    --max-num=<max>   limit number of files fetched to max
    --verbose         print subprocess calls to the shell
    -h |--help        show this message
    
    
Notes:
    ds093.0 is the original CFSR dataset, and covers from 1979 to March 2011.
    ds094.0 covers from 2011-01-01 up to the present
    
Example:
    The three steps involved in getting CFSR data are:
        python get_cfsr.py auth --email=jo.blogs@blogmail.com --passwd=NSA01 --cookie=./auth.ucar.edu
        python get_cfsr.py submit --start="2010-01-01 00:00" --end="2010-01-02 00:00" --dsid=093.0 --cookie=./auth.ucar.edu 
        python get_cfsr.py fetch BLOGS44950 BLOGS44951 --cookie=./auth.ucar.edu """

import docopt
import os
import subprocess
import sys
import re

RDA_LOGIN_SERVER = 'https://rda.ucar.edu/cgi-bin/login'
RDA_DATA_SERVER  = 'http://rda.ucar.edu'
RDA_VERIFY       = '%s/php/dsrqst-test.php' % RDA_DATA_SERVER
RDA_REQUEST      = '%s/php/dsrqst.php'      % RDA_DATA_SERVER
RDA_DATASET      = '%s/dsrqst'              % RDA_DATA_SERVER


pressure_093 = {'parameters': r'3%217-0.2-1:0.0.0,3%217-0.2-1:0.1.1,3%217-0.2-1:0.2.2,3%217-0.2-1:0.2.3,3%217-0.2-1:0.3.1,3%217-0.2-1:0.3.5',         
         'level':'76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,221,361,362,363,557,562,563,574,577,581,913,914,219',
         'grid_definition': '57',
         'product':'3',
         'grid_definition':'57',
         'ststep':'yes'}

surface_093 = {'parameters': r'3%217-0.2-1:2.0.192,3%217-0.2-1:0.3.5,3%217-0.2-1:0.2.2,3%217-0.2-1:0.2.3,3%217-0.2-1:0.1.0,3%217-0.2-1:0.1.13,3%217-0.2-1:2.0.0,3%217-0.2-1:10.2.0,3%217-0.2-1:0.3.0,3%217-0.2-1:0.0.0',
         'level':'521,522,523,524,107,223,221',
         'product':3,
         'grid_definition':62,
         'ststep':'yes'}

         
sflx_093 = {}


         
sst_093 =   {'parameters': r'3%217-0.2-1:0.0.0',
         'level':'107',
         'product':'3',
         'grid_definition':'62',
         'ststep':'yes'}         

       
pressure_094 = {'parameters': r'3%217-0.2-1:0.0.0,3%217-0.2-1:0.1.1,3%217-0.2-1:0.2.2,3%217-0.2-1:0.2.3,3%217-0.2-1:0.3.1,3%217-0.2-1:0.3.5',
               'level' :'76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,221,361,362,363,557,562,563,574,577,581,913,914,219',
               'product': '3',
               'grid_definition': '57',
               'ststep': 'yes'}
 

surface_094 = {'parameters': r'3%217-0.2-1:0.0.0,3%217-0.2-1:0.1.0,3%217-0.2-1:0.1.13,3%217-0.2-1:0.2.2,3%217-0.2-1:0.2.3,3%217-0.2-1:0.3.0,3%217-0.2-1:0.3.5,3%217-0.2-1:10.2.0,3%217-0.2-1:2.0.0,3%217-0.2-1:2.0.192',
                'level': '107,221,521,522,523,524,223',
                'product':'3',
                'grid_definition': '68',
                'ststep': 'yes'}
 
sst_094 = {'parameters': '3%217-0.2-1:0.0.0',
           'level':'107',
           'product':'3',
           'grid_definition':'68',
           'ststep':'yes'}
 
      
def main():         
    args = docopt.docopt(__doc__, sys.argv[1:])

    print args['--verbose']
    if args['auth']:
        response = authenticate(RDA_LOGIN_SERVER, args['--email'], args['--passwd'],args['--cookie'],verbose=args['--verbose'])
        #print reponse
    if args['submit']:
        print '\n\n\n****************************************'
        dsid   = args['--dsid']
        cookie = args['--cookie']
        
        options = { 'dsid': dsid,
            'startdate'   : args['--start'],
            'enddate'     : args['--end']}

        if dsid=='093.0':
            datasets = [pressure_093, surface_093]
        elif dsid=='094.0':
            datasets = [pressure_094, surface_094]
        else:
            raise Exception("unknown dataset, try 093.0 or 094.0")
        try:            
            verify_requests(datasets, options, cookie, verbose=args['--verbose'])
            if not args['--dry-run']:
                ids, indexs = submit_requests(datasets, options, cookie)
                print 'the following dataset requests were sucessfully submitted to server'
                for id, ind in zip(ids, indexs):
                    print 'ID %s' % ind
                
                print 'once these requests are available, fetch with the command'
                print '    get_cfsr.py fetch %s --cookie=%s [--out=<dir>]' %(' '.join(indexs), cookie)
                    
        except RequestError, e:
            print 'Request failure:'
            print e
        print '*****************************************'
    
    if args['fetch']:
        print '\n\n******************************************'
        print 'Fetching requests from server: %s' % RDA_DATA_SERVER
        
        
        for request_id in args['<request>']:
            # Find first occurance of digit in request
            print 'processing request: %s' % request_id
            digit = re.search("\d", request_id)

            user = request_id[0:digit.start()]
            rid   = request_id[digit.start():]    
            print '\n\n\n user: %s, id: %s' %(user, rid)
            filenames = get_filenames(RDA_DATASET, user, rid, args['--cookie'])
            if args['--verbose']:
                print 'fetching the following %d files' % len(filenames)
                for f in filenames:
                    print f
            
            if not args['--dry-run']:
                get_files(filenames, args['--cookie'], args['--out'],max_num=args['--max-num'])
        
        print 'finished fetching files'
        print 'to rename to remove date-suffix, use rename.py'
        print '*************************************************'



       
def verify_requests(datasets, options, cookie, verbose=False):         
    
    print 'verifying requests for CSFR data for WRF on pressure and surface levels'
    print 'start date: %s' % options['startdate']
    print 'end date: %s'   % options['enddate']
    print 'verifiying requests'
    for dataset in datasets:
        dataset.update(options)
        response = submit(RDA_VERIFY, dataset, cookie, verbose)
        if not 'Success' in response:
            print response
            raise RequestError(response)
        print 'request verified'

        
    

def submit_requests(datasets, options, cookie, verbose=False):         

    ids = []
    indexs = [] 
    
    print 'submitting requests for CSFR data for WRF on pressure, surface, and sst'
    print 'start date: %s' % options['startdate']
    print 'end date: %s'   % options['enddate']
    
    for dataset in datasets:
        dataset.update(options)
        response = submit(RDA_REQUEST, dataset, cookie)
        id = get_id(response)
        index = get_index(response)
        ids.append(id)
        indexs.append(index)
        
    return ids, indexs

            
            
def post_string(descr):
    """Constructs a http POST description string from dataset description"""
    
    output = "dsid=ds%(dsid)s&rtype=S&rinfo=dsnum=%(dsid)s;\
startdate=%(startdate)s;enddate=%(enddate)s;parameters=%(parameters)s;\
level=%(level)s;product=%(product)s;grid_definition=%(grid_definition)s;ststep=%(ststep)s;" % descr
    return output
    #nlat=%(nlat)s;slat=%(slat)s;wlon=%(wlon)s;elon=%(elon)s
    
def get_id(response):
    """ Parses a dataset ID from the server response"""

    print response
    lines = response.split('\n')
    id_line = [l for l in lines if "ID" in l][0]
    id       =  id_line.split(':')[1].strip()
    return id
    
def get_index(response):
    """ Parses a dataset Index from the server response"""

    lines = response.split('\n')
    id_line = [l for l in lines if "Index" in l][0]
    id       =  id_line.split(':')[1].strip()
    return id

    
def get_filenames(server, user, ind, cookie):
    """ Fetches the curl script associated with a request,
    and use it to just get a list of remote filenames"""
    
    request_id = user+str(ind)
    print request_id
    url = '%s/%s/curl.%s.csh' % (server, request_id, ind)
    out = 'curl.%s.csh' % ind
    cmd = 'curl -s -b %s %s' %(cookie, url)
    print cmd
    proc   = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    response = proc.stdout.read().rstrip('\n')
    
    #
    # We only need the lines with the id in
    # The filename is token[4]
    #
    #print response
    fnames = [l.split()[4] for l in response.split('\n') if request_id in l]
    return sorted(fnames)

    
def get_files(filenames, cookie, local_path, max_num=None):
    """ Fetches the datafiles themselves and renames them to something sensible"""

    if max_num!=None:
        filenames = filenames[0:max_num]

    for f in filenames:
        base_name = f.split('/')[-1]
        tokens = base_name.split('.')
        new_name = '%s/%s' % (local_path, base_name)
        print f + '------>' + new_name
        cmd = 'curl -s -b %s -o %s %s' % (cookie, new_name, f)
        subprocess.call(cmd, shell=True)
    

def authenticate(server, email, password, cookie, verbose=False):
    """Authenticates and saves cookie to local cookie file"""
    
    print 'authenticating at: %s' % RDA_LOGIN_SERVER
    print verbose
    cmd = 'curl -s -o /dev/null -k -s -c %s -d "email=%s&passwd=%s&action=login" %s '%(cookie, email, password, server)
    if verbose:
        print cmd
    
    proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    output = proc.stdout.read().rstrip('\n')
    return output
    

def submit(url, dataset, cookie, verbose=False):
    post_data = post_string(dataset)
    cmd = 'curl -s -b %s -d "%s" %s' % (cookie, post_data, url)
    if verbose:
        print cmd
    
    proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    output = proc.stdout.read().rstrip('\n')
    return output

    
class RequestError(Exception):
    pass    
    
if __name__ == '__main__':
    main()

