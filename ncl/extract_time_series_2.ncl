;******************************************************
; Extract time-series from WRF netcdf files write output 
; to a simple text file. Variables extracted are hard coded
; in this script, but can be turned on or off with options
; set around line 55.
;
; Credit to Dennis Shea's wrfout_to_cf.ncl for some 
; inspiration
;
; Author Sam Hawkins
; sam.hawkins@vattenfall.com
; 
;******************************************************

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRF_contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/time_axis_labels.ncl"
load "$HOME/code/wrftools/devel/ncl/wrftools.ncl"


begin

;******************************************************
; Constants / hard coded options
;******************************************************
  radians_per_degree = 0.0174532925
  extract_heights    = (/50.,60.,70.,80.,90.,100./)
  dims    = dimsizes(extract_heights)
  nlevels = dims(0)
  delete(dims)

;******************************************************

;******************************************************
; Horizontal interpolation options
; 0: none, use grid cell value from wrf_user_ll_to_ij
; 1: inverse distance weighting as implemented by rcm2points
; 2: bilinear interpolation as implemented by rcm2points
; not implemented yet
;******************************************************
  interp_option = 1


;******************************************************
; Output options
;******************************************************

;******************************************************
; Fetch some settings from environment variables
;******************************************************
  fcst_file = getenv("FCST_FILE")
  type      = getenv("NCL_OUT_TYPE")
  out_dir   = getenv("NCL_OUT_DIR")
  nest_id   = getenv("NEST_ID")    
  loc_file  = getenv("LOCATIONS_FILE")
  domain    = getenv("DOMAIN")      ; these will get used
  model_run = getenv("MODEL_RUN")   ; to write metadata


;******************************************************
; Give some info
;******************************************************
print("NCL Extracting time seres from file: "+fcst_file)


;******************************************************
; Add the file
;******************************************************
  f = addfile(fcst_file,"r")


  ;******************************************************
  ; Read locations from file with named columns
  ;******************************************************
  cmd       = "sed  '/^[[:space:]]*#/d' " + loc_file          ; skip any commented lines
  lines     = systemfunc(cmd)                                 ; take input from sed
  header    = str_split(lines(0), ",")                        ; first line is header 
  data      = lines(1:)                                       ; rest is data

  loc_ind   = str_match_ind_ic(header, "location_id")         ; find which columns to get
  lat_ind   = str_match_ind_ic(header, "latitude")            
  lon_ind   = str_match_ind_ic(header, "longitude")
  name_ind  = str_match_ind_ic(header, "name")

  loc_id    = str_get_field(data, loc_ind+1, ",")                ; str_get_field numbering starts at 1
  lat       = stringtofloat(str_get_field(data, lat_ind+1, ",")) ; so add 1 to indices
  lon       = stringtofloat(str_get_field(data, lon_ind+1, ","))
  loc_name  = str_get_field(data, name_ind+1, ",")

  delete(cmd)
  delete(lines)
  delete(header)
  delete(data)
  delete(loc_ind)
  delete(lat_ind)
  delete(lon_ind)
  delete(name_ind)
 
  dims  = dimsizes(loc_id)
  nlocs = dims(0)
  delete(dims)

  ;******************************************************
  ; Get times and dimensions
  ;******************************************************
  lat2d =f->XLAT(0,:,:)
  lon2d =f->XLONG(0,:,:)
  
  times     = f->Times
  fcst_hrs  = WRF_Times_to_udunits(times, 0)    ; using 0 forces the units to be hours since first time in the file
  init_time = chartostring(times(0,0:12))
  dims = dimsizes(fcst_hrs)
  ntimes=dims(0)
  delete(dims)

 ;******************************************************
 ; Get coordinates
 ;******************************************************
  lat2d  = f->XLAT(0,:,:)
  lon2d  = f->XLONG(0,:,:)


 ;******************************************************
 ; Get grid indices of locations of interest
 ;******************************************************
  loc   = wrf_user_ll_to_ij(f,lon, lat, True)
  loc   = loc-1          ; To convert to NCL subscripts (note this doesn't seem to work)
  dims  = dimsizes(loc)
  nlocs = dims(1)
  delete(dims)
  
  ; get using jesper's method
  jloc = wrf_user_latlon_to_ij(f, lat, lon)
  jloc = jloc - 1
  printVarSummary(loc)
  printVarSummary(jloc)
  var = f->T2(:,:,:) - 273.15
  do n=0, nlocs-1
        series = new((/ntimes,2/),"float")
        jxindex = jloc(n,1)
        jyindex = jloc(n,0)
      
        xindex = loc(0,n)
        yindex = loc(1,n)

      print("(" + xindex + "," + yindex +")" + "(" + jxindex + "," + jyindex +")")
      print(var(0,yindex, xindex))
      print(var(0,jyindex, jxindex))
      print(lat2d(yindex, xindex))
      print(lat2d(jyindex, jxindex))


       series@name      = loc_name(n)
       series@xindex    = xindex
       series@yindex    = yindex
       series@point_lat = lat(n)
       series@point_lon = lon(n)
       series@grid_lat  = lat2d(yindex, xindex)
       series@grid_lon  = lon2d(yindex, xindex)
       
       series@jxindex    = jxindex
       series@jyindex    = jyindex
       series@jgrid_lat  = lat2d(jyindex, jxindex)
       series@jgrid_lon  = lon2d(jyindex, jxindex)
      
      series(:,0)= var(:,yindex, xindex)
      series(:,1)= var(:,jyindex, jxindex)
      print(series)
      do m=0,ntimes-1
          print(series(m,0) + " " + series(m,1))
      end do
      delete(series)
      delete(xindex)
      delete(yindex)
      delete(jxindex)
      delete(jyindex)


  end do
end
