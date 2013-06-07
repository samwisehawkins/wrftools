import time, datetime
import collections
import re
from StringIO import StringIO
from odict import OrdDict
from csvtools import CommentedFile
import os

class Namelist(object):
    """Thin wrapper around a dictionary of settings, and a dictionary of sections.
    
    The Namelist.settings provides one single dictionary specifying all of the settings
    while the Namelist.sections provides a list of settings keys within each section.
    E.g. sections['domain'] = ['max_dom', 'i_parent_start', 'j_parent_start', ...]
    
    Bit of a hack, there are surely much better ways to do this"""

    def __init__(self):
       self.settings = OrdDict()
       self.sections = OrdDict()
    
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


        # single values of type string            
        if type(val)==type(''):
            return "'%s'" % val
        
        # sigle values of type bool
        elif type(val)==type(True):
            if val: return ".true."
            else:   return ".false."
        
        else:
            return str(val)
    
    
    def __str__(self):
        output = ''
        for section in self.sections.keys():
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
        
           
    def update(self, key, value, section=None):
        """ Updates the Namelist object. 
        
        If an entry already exists, it can be updated without giving a section.
        If the entry does not previously exist, the section must be given when updating. """

        if key==None:
            print 'null key given'
            raise ValueError
        if section != None:
            #
            # Section is specified
            #
            if section not in self.sections:
                #
                # We are adding a new section
                # Wrap the single setting key into a list
                #
                key_list = [key]
                self.sections[section] = key_list
            else:
                #
                # We are updating an existing section
                # but adding/modifying a settings key
                #
                key_list = self.sections[section]
                if key not in key_list:
                    # add settings key to section
                    key_list.append(key)
                    # update section list
                    self.sections[section] = key_list
        else:
            if key not in self.settings.keys():
                print 'section must be specified when adding a new key'
                raise ValueError()
        #
        # Now actually update the real settings dictionary
        #
        self.settings[key] = value



#*****************************************************************
# Namelist manipulation
#*****************************************************************

def clean_lines(fin):
    for line in fin:
        line = line.lstrip()
        line = line.rstrip('\n')
        line = line.rstrip()

        while line.endswith('\\'):
            line = line[:-1] + next(fin).rstrip('\n')
        yield line

def from_file(f):
    
    sec   = re.compile('.*&')        
    eq    = re.compile('.*=.*')             # match rows containing an equals
    evar  = re.compile('\$\{.*?\}')         # match rows containing environment vars
    lvar  = re.compile('%\(.*?\)')          # match rows containing previous definitions

    namelist_file = CommentedFile(f)
    namelist  = Namelist()
    
    current_section = 'None'

    for l in clean_lines(namelist_file):
        
        if sec.match(l):
            current_section = l.lstrip('&').rstrip()
        
        if eq.match(l):
            parts  = l.split('=')
            key_part    = parts[0].strip()
            val_part    = parts[1] 
            
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

            lvars = lvar.findall(val_part)
            if lvars!=[]:
                for lv in lvars:
                    lvname = lv[2:-1]
                    if lvname in namelist.settings:
                        val_part = val_part.replace(lv, str(namelist.settings[lvname]))            
            
            
            #
            # Parse as list, ignore any empty strings
            #
            if ',' in val_part:
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
    Namelist instance representing the settings
    
    """
        
    
    f = open(filename, 'r')
    namelist= from_file(f)
    namelist.filename = filename
    return namelist

        
def parse(str_input):
    """ Parses entries from namelist file to booelan, float, int, timestamp or string"""
    
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
#***************************************************************

#************************************************
# Directories/processors
#************************************************
&directories
log_file          = /home/slha/forecasting/operational.log
mpi_cmd           = mpirun -n %(num_procs)d -hostfile %(host_file)s 
host_file         = /home/slha/wrfmachines
base_dir          = /home/slha/forecasting/domains
backup_dir        = /longbackup/slha/forecasting/domains
wrf_dir           = /home/slha/WRFV3
wps_dir           = /home/slha/WPS
grb_dir           = /home/slha/forecasting/domains/GFS/operational
tmp_dir           = /home/slha/forecasting/tmp
upp_dir           = /home/slha/UPPV1.0
locations_file    = /home/slha/forecasting/locations/locations.csv
pcurve_dir        = /home/slha/forecasting/pcurves/fuga
archive_fmt       = '%Y-%m-%d_%H'
from_backup       = .False.       # look for output files in backup dir

#************************************************
# Metadata
#************************************************
&metadata
domain            = baseline_europe 
model             = WRF
model_run         = operational
bdy_conditions    = GFS


#************************************************
# Logging
#************************************************
debug_level       = DEBUG
mail_level        = INFO 
mailto            = sam.hawkins@vattenfall.com
mail_buffer       = 1000            # how many messages to collate in one email
mail_subject      = "Operational WRF log"

#************************************************
# Components to run
#************************************************
&share
fail_mode         = CONTINUE    # CONTINUE, EXIT
run_level         = RUN         # RUN, DUMMY
cmd_timing        = .False.
operational       = .True.      # If True, start time is based on system time
gribmaster        = .True.
sst               = .True.      # Source SST field from seperate source
wps               = .True.
wrf               = .True.
upp               = .True.      # run universal post processor 
timing            = .False.
time_series       = .False.     # Extract time series of variables to points
power             = .False.     # Calculate power production at points
met               = .False.     # Run MET verification tool
ncl               = .True.      # Run ncl visualisations
jesper            = .False.      # Run Jesper's visualisation script
archive           = .True.      # Use rysnc to copy to backup dir
cleanup           = .True.      # Run cleanup script to delete various leftovers

#*****************************************************
# SST settings
#*****************************************************
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
ncl_code_dir   = /home/slha/code/wrftools/trunk/ncl 
ncl_out_dir    = /home/slha/forecasting/domains/baseline_europe/operational/plots/%HZ        # inital time will be substitued in
web_out_dir    = /home/jepn/work/web/html/NSeaWRF/%HZ                                        # plots will be moved here after all plots done
ncl_code       = wrf_surface.ncl, wrf_radar.ncl, wrf_time_series.ncl, wrf_precip.ncl, wrf_skewt.ncl,




#********************************************************
# Archive / backup settings
# The following directories within the domain/model_run
# directory will be moved/copied to the backup directory
#********************************************************
archive_mode      = MOVE        # COPY or MOVE
backup_dirs       = wrfpost,wrfout,rsl,namelist,tseries  # which subdirs to archive


#************************************************
# Cleanup settings. The following file patterns
# from the domain/model_run directory will get 
# removed, if the cleanup flag is True
#************************************************
&cleanup
cleanup_dirs    = ${HOME}/WPS/FILE*,
test_pattern    = %(domain),


#************************************************
# Gribmaster settings
# Note that most gribmaster settings are defined in the gribmaster/conf directory
# these are just the command line options
#************************************************
&grib
gm_dir            = /home/slha/gribmaster
gm_dataset        = gfs004grb2
gm_transfer       = http
grb_fmt           = grib2
gm_delay          = 4 
convert_grb       = .False.     # convert grib1 --> grib2

#***********************************************
# Forecast settings 
#***********************************************
&forecast
max_dom            = 1
grb_input_fmt      = GFS_Global_0p5deg_%(init_time)s_fh%(fhr)s.grb,'%y%m%d_%H%M','%02d'  

#grb_input_fmt     = ECMWF_%(valid_time)s_fh000.grib, '%Y%m%d_%H'
#start             = 2006-11-30 12:00:00, 2007-03-18 00:00:00, 2007-08-12 00:00:00,
#end               = 2006-12-14 12:00:00, 2007-04-01 12:00:00, 2007-08-26 00:00:00,
#start             = 2006-11-30 12:00:00,
#end               = 2006-12-14 12:00:00,
start              = 2012-06-15 12:00:00,
end                = 2012-06-30 00:00:00,
fcst_hours        = 72
history_interval  = 60
init_interval     = 24
bdy_interval      = 6
vtable            = Vtable.GFS
#vtable           = Vtable.ECMWF
num_procs         = 24
cycles            = 00,12   # which cycles to chose from 00,06,12,18

#*****************************************************
# DFI settings - Not used unless dfi is specified in namelist
# Currently these are in minutes.  
# Usually recommended to integrate backwards one hour and
# forwards for half the time. 
#*****************************************************
dfi_bck           = 60
dfi_fwd           = 2160


#*****************************************************
# Verification
#*****************************************************
&verification
met_dir           = /home/slha/METv3.0.1
obs_file          = /home/slha/domains/obs/adpupa.nc


"""
    f = StringIO(namelist_string)
    namelist = from_file(f)
    print namelist
    
