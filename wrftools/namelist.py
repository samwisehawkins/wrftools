import time, datetime
import re
from StringIO import StringIO
import ast
from collections import OrderedDict
from commentedfile import CommentedFile
import os

class Namelist(object):
    """Class representing a FORTRAN namelist, as used for WRF configuration settings. 
    Class is composed of a dictionary of settings, and a dictionary of sections.
    
    The Namelist.settings provides one single dictionary specifying all of the settings
    while the Namelist.sections is a dictionary which maps section names to subsets of keys. 
    E.g. namelist.sections['domain'] = ['max_dom', 'i_parent_start', 'j_parent_start', ...]
    
    
    """

    def __init__(self):
        self.settings = OrderedDict()
        self.sections = OrderedDict() # maps sections to members
        self.slookup  = OrderedDict() # maps members to sections
    
    def val_to_str(self, val):
        if val=='':
            return val
            
        #
        # Process lists recursively
        #
        if type(val)==type([]):
            if len(val)==1:
                return self.val_to_str(val[0])
            
            # list of more than one element
            else:
                valstring = ''
                nvals = len(val)
                for n,v in enumerate(val):
                    if n==nvals-1:
                        vstr = ('%s' % self.val_to_str(v))
                    else:
                        vstr = ('%s,' % self.val_to_str(v)).ljust(10)
                    valstring = valstring + vstr
                return valstring


        # single values of type string. Don't put quotes around strings already in quotes
        if type(val)==type(''):
            if '"' in val:
                return val
            else:
                return "'%s'" % val
        
        # sigle values of type bool
        elif type(val)==type(True):
            if val: return ".true."
            else:   return ".false."
        
        else:
            return str(val)
    
    
    def __str__(self):
        output = ''
        for section,v in self.sections.items():
            sectionstring = '&%s\n'%section
            output+=sectionstring
            keys = self.sections[section]
            for k in keys:
                keystring = str(k).ljust(25)
                vals      = self.settings[k]
                valstring = self.val_to_str(vals)
                entrystring = ' %s = %s,\n' %(keystring, valstring)                                    
                output +=entrystring
            output+='/\n\n'
        return output
    
    
    def to_file(self, filename):
        file = open(filename, 'w')
        file.write(str(self))
        file.flush()
        file.close()
        
    def insert(self, key, value, section):
        if section==None:
            raise ValueError('must specify a namelist section for new settings')        
        
        # new section
        if section not in self.sections:
            key_list = [key]
            self.sections[section] = key_list                
        
        # existing section
        else:
            key_list = self.sections[section]
            key_list.append(key)
            self.sections[section] = key_list
        
        self.settings[key] = value
        self.slookup[key]  = section


    def update(self, key, value, section=None):
        """ Updates the Namelist object. 
        
        If an entry already exists, it can be updated without giving a section.
        If the entry does not previously exist, the section must be given. """

        if key==None:
            print 'null key given'
            raise ValueError
        
        if key not in self.settings.keys():
            self.insert(key, value, section)
        
        else:
            self.settings[key] = value


    def remove(self, key):

        if key not in self.settings:
            return
        
        section = self.slookup[key]
        key_list = self.sections[section]
        key_list.remove(key)
        
        if key_list==[]:
            del(self.sections[section])
        else:
            self.sections[section] = key_list
        del(self.settings[key])    

#*****************************************************************
# Namelist manipulation
#*****************************************************************

def clean_lines(lines):
    """ Cleans lines of trailing endlines, and joins together 
    logical continuations specified by '\\'
    
    Arguments:
        @lines -- iterable which will yield lines to be cleaned"""
    
    for line in lines:
        line = line.lstrip()
        line = line.rstrip('\n')
        line = line.rstrip()

        # join logical continuations
        while line.endswith('\\'):
            line = line[:-1] + next(lines).rstrip('\n')
        yield line

def from_file(f):
    """ Reads a namelist/configuration file and generates a 
    Namelist object. Anything enclosed in ${...} will be expanded 
    to a environment variable, while anything enclosed in 
    %(...) will be expanded to a previously defined variable within 
    the file. Anything enclosed in {} will be parsed as a string """
    
    sec   = re.compile('.*&')               # sections specified by an ampersand 
    eq    = re.compile('.*=.*')             # match rows containing an equals
    
    evar  = re.compile('\$\{.*?\}')         # match rows containing environment vars
    lvar  = re.compile('%\(.*?\)')          # match rows containing previous definitions
    dic  =  re.compile('\{.*?\}')           # match rows entirely contained in {}

    namelist_file = CommentedFile(f)
    namelist  = Namelist()
    
    #current_section = 'None'

    for l in clean_lines(namelist_file):
        
        if sec.match(l):
            
            current_section = l.lstrip('&').rstrip()
        
        if eq.match(l):
            parts  = l.split('=')
            key_part    = parts[0].strip()
            val_part    = parts[1].strip() 
            
            #
            # Substitute any environment variables
            # or previously defined terms
            #
            evars = evar.findall(val_part)
            if evars!=[]:
                for ev in evars:
                    evname = ev[2:-1]
                    if evname in os.environ:
                        val_part = val_part.replace(ev, os.environ[evname])

            #
            # Note, this means that variables need to be defined in 
            # order within the conig file.
            #
            lvars = lvar.findall(val_part)
            if lvars!=[]:
                for lv in lvars:
                    lvname = lv[2:-1]
                    if lvname in namelist.settings:
                        val_part = val_part.replace(lv, str(namelist.settings[lvname]))            
            
            
            # if it is a dictionary, enclosed in {}, parse as a string, or dict?
            # if we parse as dict, this will have slightly different syntax to 
            # other settings, e.g True will be needed rather than .True.
            if dic.match(val_part):
                vals = ast.literal_eval(val_part)


            #
            # If line contains a comma, parse as a list
            #
            elif ',' in val_part:
                tokens = val_part.split(',')
                vals   = []
                for t in tokens:
                    t = t.strip()
                    if t!='':
                        vals.append(parse(t))
            else:
                vals = parse(val_part)

            namelist.update(key_part, vals, section=current_section)

    f.close()
    return namelist

def read_namelist(filename):
    """ Reads a namelist.input file and returns a Namlist oject. 
    
    The format recognised is based on WRF namelists, with lines consisting of 
    key = val1, val2, ... valn, optionally arranged into sections specified 
    by &section headings.  Values are parsed by the wrftools.parse(str), which will 
    return the values either as string, float, int or boolean.  Dates are held as strings.
    
    Arguments:
    filename -- namelist.input filaname
    
    Returns:
    Namelist instance representing the settings"""
        
    
    f = open(filename, 'r')
    namelist= from_file(f)
    namelist.filename = filename
    return namelist



        
def parse(str_input):
    """ Parses entries from namelist file to booelan, float, int, timestamp or string
    Entries are converted to lower case, then tested in the following order:
    1. Boolean: .true. or .false.
    2. Float: contains '.'
    3. Datetime: contains '-' this could be dangerous
    4. Integer: try int()!
    5. If all of the above fail, parse as string
    
    Arguments:
        @str_input -- the string to parse
        
    Returns a parsed object (bool, float, datetime, int or string) """
    
    stripped = str_input.strip().lower()
    try:
        if stripped=='.true.':
            result = True
            return result
        elif stripped=='.false.':
            result = False
            return result
        elif '.' in stripped:
            result = float(stripped)
            return result
        elif '-' in stripped:
            result = strptime(stripped)
            return result
        else:
            result = int(stripped)
            return result
    #
    # If we can't parse it, return it as a string
    # with any quotation stripped away
    #
    except ValueError:
        return str_input.strip().replace("'", "")


def sync_namelists(namelist_wps, namelist_input):
    """ Synchronises the domain definition sections between 
    namelist.wps and namelist.input"""
    wps = read_namelist(namelist_wps)
    inp = read_namelist(namelist_input)
    
    #
    # Sync all the settings which need to be synced
    #
    for setting in ['max_dom', 'e_we', 'e_sn', 'i_parent_start', 'j_parent_start', 'parent_grid_ratio']:
        val = wps.settings[setting]
        inp.update(setting, val)
    inp.to_file(namelist_input)


def strptime(timestr):
    """ Specific implementation to convert timeformat into
    a python datetime object"""
    
    d = datetime.datetime(*time.strptime(timestr, '%Y-%m-%d %H:%M:%S')[0:5])
    return d


def test():
    namelist_string = """
#***************************************************************
# WRF Forecast Control File 
# 
# This is the top level configuration file for running 
# automated WRF forecasts. This will overide some settings in 
# 'namelist.wps' and 'namelist.input' files
#
# Environment variables can now be accessed using ${var} syntax
# Variables defined in this file can be accessed using %(syntax)
# If the variable in {} or () is not defined, it will not be expanded
#***************************************************************

#************************************************
# Metadata
#************************************************
&metadata
test1             = {'ungrib.exe': 4, 'metgrid.exe': True, 'real.exe': 6.9, 'wrf.exe': 24}
test2             = {'ungrib.exe': 4, 'metgrid.exe':4, 'real.exe': 4, 'wrf.exe': 24},{'ungrib.exe': 4, 'metgrid.exe':4, 'real.exe': 4, 'wrf.exe': 24}
domain            = baseline_europe 
model             = WRF
model_run         = development
bdy_conditions    = GFS


#************************************************
# Directories/processors. 
#************************************************
&directories
base_dir          = ${HOME}/forecasting/domains
domain_dir        = %(base_dir)/%(domain) 
model_run_dir     = %(domain_dir)/%(model_run)
wps_run_dir       = %(model_run_dir)/wps
wrf_run_dir       = %(model_run_dir)/run 
host_file         = ${HOME}/wrfmachines
log_file          = %(model_run_dir)/operational.log
backup_dir        = /longbackup/slha/forecasting/domains
wrf_dir           = ${HOME}/WRFV3_devel
wps_dir           = ${HOME}/WPS
grb_dir           = ${HOME}/forecasting/domains/GFS/operational
tmp_dir           = ${HOME}/forecasting/tmp
upp_dir           = ${HOME}/UPPV1.0
web_dir           = ${HOME}/web/html/NSeaWRF/%HZ                                        # plots will be moved here after all plots done
met_em_dir        = %(domain_dir)/met_em/%iY-%im-%id_%iH
locations_file    = ${HOME}/forecasting/locations/locations_devel.csv
pcurve_dir        = ${HOME}/forecasting/pcurves/fuga
wrftools_dir      = ${HOME}/code/wrftools/devel

#************************************************
# Logging
#************************************************
&logging
debug_level       = DEBUG
full_trace        = .True.         # whether to print a stack trace of exceptions
mail_level        = INFO 
#mailto            = sam.hawkins@vattenfall.com
mail_buffer       = 1000            # how many messages to collate in one email
mail_subject      = "Operational WRF log"

#***********************************************
# Forecast settings 
# Date syntax
# i: initial time
# v: valid time
# f: forecast 
# y,m,d,H,M,S: two-digit year, month,day,Hour,Minute,Second
# Y : four-digit year
#***********************************************
&forecast
max_dom            = 1
grb_input_fmt      = %(grb_dir)/GFS_Global_0p5deg_%iy%im%id_%iM%iH_fh%fH.grb
start              = 2013-06-14 00:00:00,
end                = 2013-06-14 00:00:00,
fcst_hours        = 6
history_interval  = 60
init_interval     = 24
bdy_interval      = 3
vtable            = Vtable.GFS
num_procs         = 8
cycles            = 00, 12,


#************************************************
# Components to run
#************************************************
&control
fail_mode         = EXIT       # CONTINUE, EXIT
run_level         = RUN        # RUN, DUMMY
cmd_timing        = .False.
operational       = .True.    # If True, start time is based on system time
prepare           = .True.
gribmaster        = .True.
sst               = .False.    # Source SST field from seperate source
wps               = .True.
ungrib            = .True.
geogrid           = .True.
metgrid           = .True.
wrf               = .True.
upp               = .False.    # run universal post processor 
timing            = .False.
power             = .False.    # Calculate power production at points
met               = .False.    # Run MET verification tool
ncl               = .True.     # Run ncl visualisations
time_series       = .True.     # Extract time series of variables to points
json              = .True.     # convert time series data to JSON
scripts           = .False.    # run additional scripts
web               = .True.     # copy plots to web out dir
archive           = .False.    # Use rysnc to copy to backup dir
summarise         = .False.    # list which files have been transferred
cleanup           = .True.     # Run cleanup script to delete various leftovers

#************************************************
# Queue settings
#***********************************************
job_template   = %(wrftools_dir)/queue/template.sge    # template to expand for SGE/PBS
job_script    = %(wrf_run_dir)/job.sge                 # expanded template gets written here
queue_name    = all.q                                  # queue to use
poll_interval = 10                                     # minutes between checking queue status  
max_job_time  = 60                                     # maximum number of hours to keep polling queue


#************************************************
# Gribmaster settings
# Note that most gribmaster settings are defined in the gribmaster/conf directory
# these are just the command line options
#************************************************
&gribmaster
gm_dir            = /home/slha/gribmaster
gm_log            = %(run_dir)/gribmaster.log
gm_dataset        = gfs004grb2
gm_transfer       = http
grb_fmt           = grib2
gm_delay          = 4 
gm_sleep          = 10         # number of minutes to wait after failure

#*****************************************************
# SST settings
#*****************************************************
&sst
sst_delay           = 24                    # number of hours SST field is delayed
sst_server          = polar.ncep.noaa.gov
sst_server_dir      = /pub/history/sst/ophi
sst_local_dir       = /home/slha/forecasting/domains/SST
sst_filename        = rtg_sst_grb_hr_0.083.%Y%m%d
sst_vtable          = Vtable.SST


#*******************************************************
# Visualisation settings
# Python will set the following environment
# variables which can be used within NCL
# FCST_FILE       - the full WRF filename 
# NCL_OUT_DIR     - output directory for plots
# LOCATIONS_FILE  - file containing locations of interest
# NEST_ID         - 2-digit integer indentifiying nest
#********************************************************
&visualisation
ncl_out_type   = png                                                                        # png, pdf etc
ncl_code_dir   = %(wrftools_dir)/ncl 
ncl_out_dir    = %(model_run_dir)/plots/%HZ        # inital time will be substitued in
ncl_code       = wrf_surface.ncl, wrf_radar.ncl, wrf_time_series.ncl, wrf_precip.ncl, wrf_t2.ncl,
ncl_code       = wrf_time_series.ncl, 
ncl_log        = %(model_run_dir)/ncl.log

#**************************************************************
# Scripts
# Run additional post-processing scripts.
# Check the code wrftools.run_scripts to see/change what 
# environment variables are available to the scripts
# currently this calls one per nest, but this is easily changed
#***************************************************************
&scripts
run_scripts    = /home/jepn/MakePlots4.csh,/home/jepn/MakePlots5.csh
tseries_code   = %(wrftools_dir)/ncl/extract_time_series.ncl, 


#********************************************************
# Archive / backup settings
# The following directories within the domain/model_run
# directory will be moved/copied to the backup directory
#********************************************************
&archive
archive_mode      = MOVE        # COPY or MOVE
backup_dirs       = wrfpost,wrfout,rsl,namelist,tseries  # which subdirs to archive


#**************************************************************
# Prepare. 
# All files matchig  patterns in pre-clean will be removed
# Subdirectories create_dirs within %(model_run_dir) will 
# be created
# All files matching patterns in wrf_links will be linked 
# from %(wrf_dir)/run to %(wrf_run_dir)
# link from and link to should be same length
#**************************************************************
pre_clean       = %(ncl_log),%(gm_log),
create_dirs     = geo_em,met_em,tseries,plots,rsl,postprd,run,wps,namelist, 
link            = %(wrf_dir)/run/*.exe           --> %(wrf_run_dir),\
                  %(wrf_dir)/run/RRTM*           --> %(wrf_run_dir),\
                  %(wrf_dir)/run/*.TBL           --> %(wrf_run_dir),\
                  %(wps_dir)/*.exe               --> %(wps_run_dir),\
                  %(wps_dir)/link_grib.csh       --> %(wps_run_dir),\
                  %(wps_dir)/metgrid/METGRID.TBL -->%(wps_run_dir)

#************************************************
# Cleanup settings. The following file patterns
# will get removed using rm -f if the cleanup flag is True
# BE VERY CAREFUL SPECIFYING!
# You could easily wipe a directory
#************************************************
&cleanup
post_clean     = %(wps_dir)/FILE*, %(wps_dir)/GFS*, %(wps_dir)/PFILE*, \
                  %(wps_dir)/geogrid.log*, %(wps_dir)/metgrid.log*,\
                  %(wrf_dir)/run/rsl.error.*, %(wrf_dir)/run/rsl.out.*,

#************************************************
# Gribmaster settings
# Note that most gribmaster settings are defined in the gribmaster/conf directory
# these are just the command line options
#************************************************
&gribmaster
gm_dir            = ${HOME}/gribmaster
gm_log            = %(model_run_dir)/gribmaster.log
gm_dataset        = gfs004grb2
gm_transfer       = http
grb_fmt           = grib2
gm_delay          = 4 
gm_sleep          = 0.1         # number of minutes to wait after failure
gm_max_attempts   = 3           # number of times to try before giving up
convert_grb       = .False.     # convert grib1 --> grib2


#*****************************************************
# DFI settings - Not used unless dfi is specified in namelist
# Currently these are in minutes.  
# Usually recommended to integrate backwards one hour and
# forwards for half the time. 
#*****************************************************
&dfi
dfi_bck           = 60
dfi_fwd           = 2160


#*****************************************************
# Verification
#*****************************************************
&verification
met_dir           = /home/slha/METv3.0.1
obs_file          = /home/slha/domains/obs/adpupa.nc




"""
    #f = StringIO(namelist_string)
    #namelist = from_file(f)
    namelist = read_namelist('/home/slha/forecasting/domains/aberdeen/resource/namelist.input')
   
    print namelist
    print '\n'
    

    
if __name__ == "__main__":
    test()        