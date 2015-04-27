import string   
import pandas as pd
import numpy as np
from netCDF4 import Dataset, MFDataset
from netCDF4 import num2date, date2num
import datetime
import loghelper
import json

LOGGER = "ncdump"
HGT2DNUM      = 9999   # height to encode 2D variables as (must be numeric and not clash with real heights)
HGT2DSTR      = "2D"   # how 2D vars are specified in config file (can be string)

class UnknownFormat(Exception):
    pass

class ConfigError(Exception):
    pass

class DatasetError(Exception):
    pass
    
def get_coordinate_vars(dataset, coords=None):
    """ Gets coordinate variables associated with dimensions,
    doing some conversion to character array and time units
    
    Arguments:
      dataset -- a NetCDF4 Dataset object
      coords  -- a list of variable names to treat as coordinates. If None, then 
                 coordinate variables are selected based on dimension names"""
    
    logger = loghelper.get(LOGGER)
    logger.debug("get_coordinate_vars()")
    
    dims = dataset.dimensions
    vars = dataset.variables
    ndims = len(dims)
    
    
    
    # if coordinate variables are not specified, fetch all variables 
    # with the same name as dimensions (it they exist)
    if not coords:
        logger.debug("no coordinate variables given, finding automatically")
        coords = [ d for d in dims if vars.get(d) ] 


    # package the result as a dictionary 
    result = {}
        
    for c in coords:
        cvar = vars[c]
        
        if str(cvar.dtype)=="|S1":
            result[c] = _char_array_to_str(cvar)
        elif _is_time(cvar):
            result[c] = num2date(cvar[:], units=cvar.units,calendar=cvar.calendar)
        else:
            result[c] = cvar[:]
    return result


def melt(ncfiles, vars=None, global_atts=None,var_atts=None, coord_vars=None, missing=None):

    """ Build a (molten) Pandas DataFrame from a series of netcdf files. This is a flexible, but very 
    memory-inneficient data structure, so be careful calling this with large netcdf files.
    
    Arguments:
      ncfiles     -- the input filenames
      vars        -- the variables to read, if None all variables in files read
      var_atts    -- variable attributes to include in each line of output, default all
      global_atts -- global attributes to include in each row of output
      coord_vars  -- variables to treat as coordinates, if None will use variables with 
                     the same name as dimensions"""

    logger = loghelper.get_logger(LOGGER)
    frames = []

        
    if len(ncfiles)==1:
        dataset = Dataset(ncfiles[0])
    else:
        dataset = MFDataset(ncfiles)
    
    
    coord_vars = get_coordinate_vars(dataset, coord_vars)
    variables = dataset.variables
    
    # get global attributes in dataset
    # shouldn't really use this, but it works
    dataset_atts = dataset.__dict__
        

    use_global_atts = _lookup(global_atts, dataset_atts, missing)

    
    
    # if no vars specified, use all in ncfiles
    if (vars==None or vars==["all"]):  vars = list(variables.keys())
    
    
    
    # variables are a function of var(reftime,leadtime,height,location)
    # or var(reftime,leadtime,location)
    usevars = [v for v in vars if v not in coord_vars]
    
   
    logger.debug("usevars: %s" % usevars)

    # There must be a clean way of doing this in a general 
    # way, but I don't have the time to code this properly,
    # so I'm looping over fixed and hard-coded dimension names
    
    location = coord_vars['location']
    reftime  = coord_vars['reftime']
    leadtime = coord_vars['leadtime']
    height   = coord_vars['height']
    #lat      = coord_vars['lat']
    #lon      = coord_vars['lon']
    
    nloc = len(location)
    nreftime = len(reftime)
    nleadtime = len(leadtime)
    
    # dimension order is reftime, leadtime, location, height
    # or reftime, leadtime, location
    vars2D = [v for v in usevars if len(variables[v].shape)==3]
    vars3D = [v for v in usevars if len(variables[v].shape)==4]
    
    series = []
    
    for v in vars2D:
        vname = v
        variable = variables[v]

        use_var_atts = _lookup(var_atts, variable.__dict__, missing)
        
        factors = [reftime, leadtime, [HGT2DNUM], location, [vname]] + map(_listify, use_global_atts.values()) + map(_listify,use_var_atts.values())
        names = ['reftime', 'leadtime', 'height', 'location','variable'] + use_global_atts.keys() + use_var_atts.keys()
        
        index = pd.MultiIndex.from_product(factors, names=names)
        #index = pd.MultiIndex.from_tuples([(ref,lead,loc,HGT2DNUM,vname) for ref in reftime for lead in leadtime for loc in location], names=['reftime', 'leadtime', 'location', 'height','variable'])
        
        if type(variable[:]) == np.ma.core.MaskedArray:
            data = variable[:].flatten().filled(np.nan).astype(np.float)
        else:
            data = variable[:].flatten().astype(np.float)

        series.append( pd.Series(data=data, index=index, name='value'))

    for v in vars3D:
        variable = variables[v]
        vname = v
        use_var_atts = _lookup(var_atts, variable.__dict__, missing)
        for h,hgt in enumerate(height):
            subvar = variable[:,:,:,h]
            vname = "%s.%03d" % (v,hgt)
            vname = v
            factors = [reftime, leadtime, [hgt], location, [vname]] + map(_listify, use_global_atts.values()) + map(_listify,use_var_atts.values())
            names = ['reftime', 'leadtime', 'height', 'location','variable'] + use_global_atts.keys() + use_var_atts.keys()
            index = pd.MultiIndex.from_product(factors, names=names)
            #index = pd.MultiIndex.from_tuples([(ref,lead,loc,hgt,vname) for ref in reftime for lead in leadtime for loc in location], names=['reftime', 'leadtime', 'location','height', 'variable'])
            if type(subvar) == np.ma.core.MaskedArray:
                data = subvar[:].flatten().filled(np.nan).astype(np.float)
            else:
                data = subvar[:].flatten().astype(np.float)
            
            series.append(pd.Series(data=data, index=index, name='value'))
    
    
    # this is molten data, to use Haldey Wickham's terminology
    # or perhaps 5th normal form?
    result = pd.concat(series, axis=0).reset_index()
    return result
    
def _parse_filter(filter_str):
    return map(float, filter_str.split(':'))

    
def filter(frame, rules):
    """ Filters a data frame according to a set of rules specified in rules i.e. 
    'column name' : [list of values] |
    'column name' : tuple of numeric limits (min, max)
    
        Arguments:
        frame   -- the DataFrame to filter
        rules   -- rules to apply """        
    
    
    
    logger = loghelper.get(LOGGER)
    
    logger.debug("%d rows before filtering" % len(frame))
    logger.debug(json.dumps(rules, indent=4))
    for column, rule in rules.items():
        logger.debug("filtering on %s" % column)
        
        # if a list of values is provided, filter on those
        if type(rule)==list:
            frame = frame[frame[column].isin(rule)]
        
        # else if a tuple is provided, treat those as min, max values
        elif type(rule)==str:
            min, max = _parse_filter(rule)
            frame = frame[(frame[column]>=min) & (frame[column]<=max)]
    
        else:
            raise ConfigError("filter type not understood, please give list or tuple")

        logger.debug("%d rows" % len(frame))            
    
    return frame

def _listify(element):
    """ Ensures elements are contained in a list """
    
    # either it is a list already, or it is None
    if type(element)==type([]) or element==None:
        return element
    
    else:
        return [element]

def concat(frame, cols, name=None, delim=".", formatter=None, drop=True, inplace=True):
    
    if name==None: name = delim.join(cols)
    
    if not inplace:frame = frame.copy()
    
    vals = _concat_cols(frame, cols, delim=delim, formatter=formatter)
    _drop_inplace(frame, cols)
    frame[name] = vals
    
    if not inplace: return frame

    
def _concat_cols(frame, cols, delim='.', formatter=None):
        """ mashes two columns into one by concantenating their columns. Default applies 
        str to each column and separates with a dot
        
        Arguments:
          frame     -- data frame to operate on
          cols      -- list of columns to join
          delimiter -- delimiter to use to sepearate values 
        """
        logger = loghelper.get(LOGGER)
        logger.warn("Peformance warning, string concatenation of columns not done very efficiently")
        
        if len(cols)!=2:
            raise NotYetImplemented("concatenating other than two columns is not yet implemented")
        
        if formatter!=None:
            if type(formatter==type([])):
                result = frame[cols[0]].apply(formatter[0]) + delim +  frame[cols[1]].apply(formatter[1])
            
            elif type(formatter==type({})):
                result = frame[cols[0]].apply(formatter[cols[0]]) + delim +  frame[cols[1]].apply(formatter[cols[1]])        
        else:
            result = frame[cols[0]].map(str) + delim +  frame[cols[1]].map(str)
        
        return result


def _lookup(keys, target, missing):
    
    result = {}
    for key in keys:
        # the attribute really is there
        if key in target:
            result[key] = target[key]
        
        # else it is missing, but a default has been provided
        elif key in missing:
            result[key] = missing[key]
        
        # else we are screwed, and should probably raise an exception
        else:
            raise KeyError("attribute not found and no default missing value given")

    return result
    
def _valid_time(reftime, leadtime):

 
    refdt     = num2date(reftime[:], units=reftime.units, calendar=reftime.calendar)
    inittime  = refdt[0]
    
    if "hour" in leadtime.units:
        delta = datetime.timedelta(0,60*60)
    
    elif "minute" in leadtime.units:
        delta = datetime.timedelta(0,60)

    else:
        raise FileInputError("leadtime units of %s not supported" % leadtime.units) 

    validtime = refdt[:] + (leadtime[:] * delta)        
    return validtime
    
def _char_array_to_str(chars):
    """Converts a NetCDF masked character array into an array of strings"""
    logger = loghelper.get(LOGGER)
    # assert we have two dimensions
    assert(len(chars.shape)==2)
    dim0 = chars.shape[0]
    dim1 = chars.shape[1]
    

    # if it is a masked array, replace masked with blanks
    if hasattr(chars[:], 'mask'):
        # first fill in masked elements with blanks
        
        filled = chars[:].filled(' ')
    else: 
        filled = chars

    # join character arrays across last dimension
    strs = [''.join(filled[n,:]) for n  in range(dim0) ]        
    
    # then strip away the blanks
    strs = map(string.strip, strs)
    
    # return as an array of strings 
    return np.array(strs)

def _is_time(variable):
    """Determines whether a NetCDF variable represents time"""
    
    return hasattr(variable, 'calendar')

def _drop_inplace(frame, cols):
    lcols = _listify(cols)
    for c in lcols:
        del(frame[c])
    
def _drop(frame, cols):
    lcols = _listify(cols)
    new_cols = [c for c in frame.columns if c not in lcols]
    return frame[new_cols]

def _rename(frame, mapping):
    new_names = [ mapping[c] if c in mapping else c for c in frame.columns]
    frame.columns = new_names
    return frame