;******************************************************
; Extract time-series from WRF gridded netcdf files write output 
; to netcdf files where location is a dimension.
;
; The variables in the resulting NetCDF files will be 
; of the form 3DVar(location, height, time)
;             2DVar(location, time)
;
; i.e. location is the record dimension. This could be changed 
; in future if there is a need for that
;
; Credit to Dennis Shea's wrfout_to_cf.ncl for some inspiration
;
;
; Author Sam Hawkins, Jesper Nissen
; sam.hawkins@vattenfall.com
; 
;******************************************************
load "$HOME/code/wrftools/devel/ncl/wrftools.ncl"

begin

;******************************************************
; Either get input from command-line options (preference)
; or environment variables
;******************************************************
  in_file    = getenv("FCST_FILE")
  out_dir    = getenv("NCL_OUT_DIR")
  out_file   = getenv("NCL_OUT_FILE")
  var_file   = getenv("NCL_VAR_FILE")
  loc_file   = getenv("LOCATIONS_FILE")
;******************************************************

    
;******************************************************
; Constants / hard coded options
;******************************************************
  if .not. isdefined("extract_heights") then 
      extract_heights = (/80.0,100.0/)      
  end if
  

  dims    = dimsizes(extract_heights)
  nhgts   = dims(0)
  delete(dims)
;******************************************************

;******************************************************
; Dimension ordering. Currently not used, dimension 
; ordering is hardcoded in wrftools.ncl
; but would be useful to have it here at some point
;*****************************************************

  if .not. isdefined("dim_order_2D") then
      dim_order_2D =(/"time", "location"/)
  end if 
  
  if .not. isdefined("dim_order_3D") then
      dim_order_3D = (/"time", "location", "height"/)
  end if

  
;******************************************************
; Options
  opts = True
;******************************************************  
    ;**************************************************
    ; Horizontal interpolation options
    ; 0: none, use grid cell value from wrf_user_ll_to_ij (not implemented yet!)
    ; 1: inverse distance weighting as implemented by rcm2points(opt=1)
    ; 2: bilinear interpolation as implemented by rcm2points(opt=2)
    ;**************************************************
    opts@interp_option = 2

    ;**************************************************
    ; Time units
	opts@time_units = 1 
    ;                 0 units of "hours since" initial time on the current file (type "double")
    ;                 1 returns units of "hours since 1901-01-01 00:00:00" (type "double")
    ;                 2 returns units of "yyyymmddhhmnss" (type "double")
    ;                 3 returns units of "yyyymmddhh" (type "integer")
    ;**************************************************

    
    ;**************************************************
    ; Bulk richardson options. 
    ; TODO, allow these to be arrays, 
    ; so we can do multiple heights
    ; rib_opt=1        ; AMS versions 
	opts@rib_opt=2     ; Zilintikivich et al
    ;opts@rib_h_lower = 50.0     ; lower height must be of the interpolation heights
    ;opts@rib_h_upper = 100.0    ; upper height
    opts@rib_i_lower = 2         ; lower (extract_height) index
    opts@rib_i_upper = 4         ; upper (extract_height) index
    ;**************************************************

;******************************************************  


;******************************************************
; Output Variables. 
;******************************************************
    load "$NCL_VAR_FILE"



;******************************************************
; Give some info
;******************************************************
;print("NCL Extracting time series from file(s): "+in_file)
;******************************************************




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

    
print("*** SUCCESS NCL EXTRACT TIME SERIES ***")    
end





