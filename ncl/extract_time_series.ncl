;******************************************************
; Extract time-series from WRF gridded netcdf files to 
; netcdf files where location is a dimension.
;
; The variables in the resulting NetCDF files will be 
; of the form 3DVar(time,location,height)
;             2DVar(time, location)
;
; Usage:  Arguments can be specified either on the command line
; or by setting environment variables. Command line definitions
; will override environment variables.
;
; The following arguments/environment variables are used:
;
; Command line arg  Env variable      Description
; in_file           FCST_FILE         a single input file or array of input files
; out_dir           NCL_OUT_DIR       a single output directory
; out_file          NCL_OUT_FILE      the name of an output file
; loc_file          LOCATIONS_FILE    the name of a locations file specifying locations
;                   NCL_OPT_FILE      a snippet of ncl code which will get loaded,
;                                     defining options and variables. Must be env variable.
;
; Credit to Dennis Shea's wrfout_to_cf.ncl for some inspiration
;
; Author Sam Hawkins
; sam.hawkins@vattenfall.com
; 
;******************************************************
load "$HOME/code/wrftools/devel/ncl/wrftools.ncl"

begin

;******************************************************
; Either get input from command-line options (preference)
; or environment variables
; Strategy. If the variable is directly 
; defined on the command-line, then that takes preference.
; Otherwise we take it from an environment variable.

;******************************************************
    if .not. isdefined("in_file") then 
        in_file = getenv("FCST_FILE") 
    end if

    if .not. isdefined("out_dir") then 
        out_dir    = getenv("NCL_OUT_DIR")
    end if

    if .not. isdefined("out_file") then 
        out_file   = getenv("NCL_OUT_FILE")
    end if 
    
    if .not. isdefined("loc_file") then 
        loc_file   = getenv("LOCATIONS_FILE")
    end if
    
    ; this must be defined as a environment variable
    ; due to the way a load statement works in NCL
    opt_file   = getenv("NCL_OPT_FILE")

    
    ;******************************************************
    ; Default height options hard-coded
    ;******************************************************
    if .not. isdefined("extract_heights") then 
        extract_heights = (/20.0,40.0,60.0,80.0,100.0,150.0,200.0/)      
    end if
  
;******************************************************
 
 
;******************************************************
; Work out number of heights  
;******************************************************
  dims    = dimsizes(extract_heights)
  nhgts   = dims(0)
  delete(dims)
;******************************************************

;******************************************************
; Dimension ordering. Currently not used, dimension 
; ordering is hardcoded in wrftools.ncl
; but would be useful to have it here at some point
;*****************************************************
;
;  if .not. isdefined("dim_order_2D") then
;      dim_order_2D =(/"time", "location"/)
;  end if 
;  
;  if .not. isdefined("dim_order_3D") then
;      dim_order_3D = (/"time", "location", "height"/)
;  end if
;*****************************************************
  
;******************************************************
; Options and output variables
; Load these at run-time to avoid hard-coding options
; into the script.
;******************************************************  
    load "$NCL_OPT_FILE"
;******************************************************

;******************************************************
; Give some info
;******************************************************
print(in_file)
print(out_file)
;******************************************************

;******************************************************
; Remove output file
;******************************************************
if (isfilepresent(out_file))
    print("NCL remving pre-existing output file")
    system ("rm -f " + out_file )
end if



;******************************************************
; Add the file(s)
; Only used addfiles if there is more than one file
;******************************************************
	dims = dimsizes(in_file)
    nfiles = dims(0)
    delete(dims)
  
    if (nfiles.eq.1) then 
        f = addfile(in_file(0),"r")
    else 
        f = addfiles(in_file, "r")
    end if 
 
    locations = read_locations(loc_file)
    loc_id = locations[0]
	name   = locations[1]
	lat    = locations[2]
	lon    = locations[3]
	
    ;print(loc_id)
    dims=dimsizes(loc_id)
    nlocs = dims(0)
    delete(dims)	

    ;print("Read " + nlocs+ " locations from file: " + loc_file)
    ; What do we call out_file?
    ;out_file = out_dir +"/tseries_" + init_time +".nc"
    
    fout = wrf_user_interp_vars_tofile(f, extract_heights,loc_id, lat, lon,-1,out_file, vars, opts)
    printVarSummary(fout)
    delete(fout)
    
print("*** SUCCESS NCL EXTRACT TIME SERIES ***")    
end





