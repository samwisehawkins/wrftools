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
; Command line arg  Description
; ncl_in_file       a single input file or array of input files
; ncl_out_dir       a single output directory
; ncl_out_file      the name of an output file
; ncl_loc_file      the name of a locations file specifying locations
;
; Credit to Dennis Shea's wrfout_to_cf.ncl for some inspiration
;
; Author Sam Hawkins
; sam.hawkins@vattenfall.com
; 
;******************************************************

; This is a library which contains custom code for interpolating
; time-series to locations. It is loaded like this as we can't 
; rely on it being in a central location. To run this script, 
; set the NCL_WRFTOOLS environment variable to point to the 
; correct location.

load "ncl/wrftools.ncl"

begin

;******************************************************
; Get options from file
;******************************************************
    
    ; this must be defined as a environment variable
    ; due to the way a load statement works in NCL
    ;opt_file   = getenv("NCL_OPT_FILE")
    load "$NCL_OPT_FILE"
    ncl_in_file = getenv("NCL_IN_FILE")
    ncl_out_file = getenv("NCL_OUT_FILE")
    ncl_out_type = getenv("NCL_OUT_TYPE")
    ncl_loc_file = getenv("NCL_LOC_FILE")

;******************************************************

    ; test whether filename has .nc extension, and if not
    ; we add it
    extension = str_match(ncl_in_file, ".nc")
    if ismissing(extension) then
        print("adding file extension")
        ncl_in_file = ncl_in_file+".nc"
        print(ncl_in_file)
    end if

    extension = str_match(ncl_out_file, "."+ncl_out_type)
    if ismissing(extension) then
        print("adding file extension")
        ncl_out_file = ncl_out_file+"."+ncl_out_type
        print(ncl_out_file)
    end if



    
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
; Give some info
;******************************************************
print(ncl_in_file)
print(ncl_out_file)
;******************************************************

;******************************************************
; Remove output file
;******************************************************
if (isfilepresent(ncl_out_file))
    print("NCL remving pre-existing output file")
    system ("rm -f " + ncl_out_file )
end if



;******************************************************
; Add the file(s)
; Only used addfiles if there is more than one file
;******************************************************
	dims = dimsizes(ncl_in_file)
    nfiles = dims(0)
    delete(dims)
  
    if (nfiles.eq.1) then 
        f = addfile(ncl_in_file(0),"r")
    else 
        f = addfiles(ncl_in_file, "r")
    end if 

    locations = read_locations(ncl_loc_file)
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
    
    fout = wrf_user_interp_vars_tofile(f, extract_heights,loc_id, lat, lon,-1,ncl_out_file, vars, tsopts)
    delete(fout)
    
print("*** SUCCESS NCL EXTRACT TIME SERIES ***")    
end





