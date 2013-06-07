;load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
;load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/skewt_func.ncl"
;load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"

begin

;******************************************************
; Read locations from file 
;******************************************************
  home           = getenv("HOME")
  
  locations_file = home + "/forecasting/locations/locations.csv"
  
  cmd       = "sed  '/^[[:space:]]*#/d' " + locations_file    ; skip any commented lines
  lines     = systemfunc(cmd)
  header    = str_split(lines(0), ",")                        ; first line is header 
  data      = lines(1:)                                       ; rest is data

  loc_ind   = str_match_ind_ic(header, "location_id")         ; find which columns to get
  lat_ind   = str_match_ind_ic(header, "latitude")            
  lon_ind   = str_match_ind_ic(header, "longitude")
  name_ind  = str_match_ind_ic(header, "name")

  loc_id    = str_get_field(data, loc_ind+1, ",")                ; str_get_field numbering starts at 1
  lat       = stringtofloat(str_get_field(data, lat_ind+1, ",")) ; so add 1 to indices
  lon       = stringtofloat(str_get_field(data, lon_ind+1, ","))
  name      = str_get_field(data, name_ind+1, ",")
  print(loc_id)
  print(name)
  print(lat)
  print(lon)
end
