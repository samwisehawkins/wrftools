""" Requests subsets of CFSR data, fetches to local storage and renames"""
import os
import subprocess

#
# User options
#
DSID             = '093.0'
RDA_LOGIN_SERVER = 'https://rda.ucar.edu/cgi-bin/login'
RDA_DATA_SERVER  = 'http://rda.ucar.edu'
RDA_VERIFY       = '%s/php/dsrqst-test.php' % RDA_DATA_SERVER
RDA_REQUEST      = '%s/php/dsrqst.php'      % RDA_DATA_SERVER
RDA_DATASET      = '%s/dsrqst'              % RDA_DATA_SERVER
LOCAL_DIR        = '/home/slha/forecasting/data/reanalysis/CSFR'
COOKIE           = '/home/slha/auth.ucar.edu'
START            = '2010-01-01 00:00'
END              = '2011-01-02 00:00'
EMAIL            = 'sam.hawkins@vattenfall.com'
PASSWORD         = 'slh561944'
NLAT='70';  
SLAT='40'; 
WLON='-030'; 
ELON='030'; 


options = { 'dsid':DSID,
            'startdate':START,
            'enddate': END,
            'nlat':    NLAT,  
            'slat':    SLAT, 
            'wlon':    WLON,
            'elon':    ELON}

plevs = {'parameters': r'3%217-0.2-1:0.0.0,3%217-0.2-1:0.1.1,3%217-0.2-1:0.2.2,3%217-0.2-1:0.2.3,3%217-0.2-1:0.3.1,3%217-0.2-1:0.3.5',         
         'level':'76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,221,361,362,363,557,562,563,574,577,581,913,914,219',
         'grid_definition': '57',
         'product':'3',
         'grid_definition':'57',
         'ststep':'yes'}

surface = {'parameters': r'3%217-0.2-1:2.0.192,3%217-0.2-1:0.3.5,3%217-0.2-1:0.2.2,3%217-0.2-1:0.2.3,3%217-0.2-1:0.1.0,3%217-0.2-1:0.1.13,3%217-0.2-1:2.0.0,3%217-0.2-1:10.2.0,3%217-0.2-1:0.3.0,3%217-0.2-1:0.0.0',
         'level':'521,522,523,524,107,223,221',
         'product':3,
         'grid_definition':62,
         'ststep':'yes'}

sst =   {'parameters': r'3%217-0.2-1:0.0.0',
         'level':'107',
         'product':'3',
         'grid_definition':'62',
         'ststep':'yes'}         

         
def main():         

    ids, indexs = submit_requests()
   
    indexs = ['42402', '42403', '42404'] 
    ids = ['HAWKINS%s' % i for i in indexs]
    
    filenames = get_filenames(RDA_DATASET, 'HAWKINS42402', '42402', COOKIE)
    get_files(filenames, COOKIE, LOCAL_DIR, 'surface')
    
    filenames = get_filenames(RDA_DATASET, 'HAWKINS42403', '42403', COOKIE)
    get_files(filenames, COOKIE, LOCAL_DIR, 'pressure')

    filenames = get_filenames(RDA_DATASET, 'HAWKINS42404', '42404', COOKIE)
    get_files(filenames, COOKIE, LOCAL_DIR, 'sst')
    

def fetch_dataset(server, ids, indexs, cookie):
    """ Fetches data which is already subset and waiting on the server """
    
    for id, index in zip(ids, indexs):
        filenames = get_filenames(server, id, index, cookie)
        get_files(filenames, COOKIE, LOCAL_DIR, 'surface')
    

def submit_requests():            

    ids = []
    indexs = [] 
    print '\n\n****************************'
    print 'submitting requests for CSFR data for WRF on pressure, surface, and sst'
    print 'user: %s' % EMAIL
    print 'start date: %s' % options['startdate']
    print 'end date: %s'   % options['enddate']
    print 'verifiying requests'
    for dataset in (plevs, surface, sst):
        dataset.update(options)
        response = submit(RDA_VERIFY, dataset, COOKIE)
        if not 'Success' in response:
            raise RequestError(response)
        print 'request verified'
    print 'All requests verified'
    
    print 'submitting requests to data server'
    for dataset in (plevs, surface, sst):        
        response = submit(RDA_REQUEST, dataset, COOKIE)
        id = get_id(response)
        index = get_index(response)
        ids.append(id)
        indexs.append(index)
    print 'submitted the followinf requests:'
    
    for (id,index) in ids, indexs:
        print '\t%s\t%s' % index, id
    return ids, indexs
    print '****************************\n\n'            
            
            
            
            
def post_string(descr):
    """Constructs a http POST description string from dataset description"""
    
    output = "dsid=ds%(dsid)s&rtype=S&rinfo=dsnum=%(dsid)s;startdate=%(startdate)s;enddate=%(enddate)s;parameters=%(parameters)s;level=%(level)s;product=%(product)s;grid_definition=%(grid_definition)s;ststep=%(ststep)s" % descr
    return output

def get_id(response):
    """ Parses a dataset ID from the server response"""

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

    
def get_filenames(server, id, index, cookie):
    """ Fetches the curl script associated with a request,
    and use it to just get a list of remote filenames"""
    url = '%s/%s/curl.%s.csh' % (server, id, index)
    out = 'curl.%s.csh' % index
    cmd = 'curl -b %s %s' %(cookie, url)
    print cmd
    proc   = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    response = proc.stdout.read().rstrip('\n')
    
    #
    # We only need the lines with the id in
    # The filename is token[4]
    #
    fnames = [l.split()[4] for l in response.split('\n') if id in l]
    
    return fnames

    
def get_files(filenames, cookie, local_path, local_prefix):
    """ Fetches the datafiles themselves and renames them to something sensible"""
    for f in filenames:
        base_name = f.split('/')[-1]
        tokens = base_name.split('.')
        tokens[3] = local_prefix
        new_name = local_path+'/'+'.'.join(tokens)
        print f + '------>' + new_name
        cmd = 'curl -b %s -o %s %s' % (cookie, new_name, f)
        subprocess.call(cmd, shell=True)
    
def authenticate(server, email, password, cookie):
    """Authenticates and saves cookie to local cookie file"""
    
    cmd = 'curl -o /dev/null -k -s -c %s -d "email=%s&passwd=%s&action=login" %s '%(cookie, email, password, server)
    print cmd
    proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    output = proc.stdout.read().rstrip('\n')
    return output
    

def submit(url, dataset, cookie):
    post_data = post_string(dataset)
    cmd = 'curl -b %s -d "%s" %s' % (cookie, post_data, url)
    print cmd
    proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    output = proc.stdout.read().rstrip('\n')
    return output

    
class RequestError(Exception):
    pass    
    

if __name__ == '__main__':
    main()    
