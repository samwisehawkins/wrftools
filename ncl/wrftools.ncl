load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/ut_string.ncl"


;************************************************************
; Expects the variable to have dimensions time * level * sn * ew
; opt = 0 interpolates wind components seperately
;************************************************************

undef("wrf_interp_agl")
function wrf_interp_agl(a:file, varin[*]:string, anem_hgt:numeric, opt:integer)
local var, varz, ter, ua, va, uz, vz

begin
    ter           = wrf_user_getvar(a, "ter", 0)      ; assume terrain doesn't change with time
    hgt_amsl      = wrf_user_getvar(a, "z", -1)       ; height above sea level of model levels
                                                      ; this will be 4D, since height varies (slightly)

    new_hgt = conform(hgt_amsl, ter, (/2,3/))         ; ensure they terrain height is right dimensionality
    hgt_agl = hgt_amsl - new_hgt                      ; get the height of model levels above ground level

    ;
    ; If the variable is speed, then we need to get the components 
    ; seperately then compute speed.  Take note, this means we 
    ; interpolate speed from height, not components seperately
    ; Need to think about the physical meaning of this
    ;
    if(varin.eq."speed") then 
      ;ua = wrf_user_getvar(a, "ua", -1)             ; wind components averaged (unstaggered) to mass points. These are not rotated!
      ;va = wrf_user_getvar(a, "va", -1)             ; wind components averaged (unstaggered) to mass points
      
      ua = wrf_user_getvar(a, "uvmet", -1)          ; these are rotated, but are they unstaggered?
      va = wrf_user_getvar(a, "uvmet", -1)             ;
      
      ;
      ; Interpolate components seperately
      ; 
      if opt.eq.0 then
        uz = wrf_user_intrp3d(ua, hgt_agl, "h", anem_hgt,0, False) 
        vz = wrf_user_intrp3d(va, hgt_agl, "h", anem_hgt,0, False) 
          varz = sqrt(uz^2+vz^2)

        else 
            var = sqrt(ua^2+va^2)
            varz = wrf_user_intrp3d(var, hgt_agl, "h", anem_hgt,0,False) 
        end if
        
    else 
        var = wrf_user_getvar(a, varin, -1)
        varz = wrf_user_intrp3d(var, hgt_agl, "h", anem_hgt,0,False) 
    end if

    varz!0 = "time"
    varz!1 = "height"
    varz&height = anem_hgt
    
    return varz

end


;**************************************************************
; Writes an ascii representation of a time series for a 
; two-dimensional variable where first dimension is time, 
; Writes to record-based tseries format: 
; domain, model_run, model, nest_id, init_time, valid_time, variable, location_id, latitude, longitude, height, value
; 
; Propose new format (use headers!):
; domain, model_run, model, nest_id, location_id, latitude, longitude, variable, init_time, valid_time, height, value
;
; If we want this in JSON, for web charts, use a parser in Python
; making NCL write JSON is ugly.
;
; Either we can explicitly define the parameters domain, model_run etc, OR we could just 
; pass in a string array of 'metadata' to get get written on each row, OR
; we could add the metadata as attributes to the variable, speed.domain.
;
; For now, pass in metdata, data, location_ids, lats, lons. 
; Bit messy but WTF.
;
;***************************************************************

undef("write_series")
procedure write_series(series[*]:numeric,fname:string)

begin
    
    dims    = dimsizes(series)
    ntimes  = dims(0) 
    time    = series&time
    delete(dims)
    header = (/"domain","model_run","model","nest_id","location_id","location_name","latitude","longitude","variable","init_time","valid_time","height","value"/)
    prefix  = series@domain + "," + series@model_run + "," + series@model + "," + series@nest_id + "," + series@loc_id + "," + series@loc_name + "," + series@lat + "," + series@lon + "," +series@var_name
    ;print(prefix)
    
    
    timestrs = ut_string(time, "%Y-%N-%D %H:%M:%S") ; convert times to strings
    output   = new(ntimes+1, "string")
    output(0) = str_join(header, ",")
    do i=0,ntimes-1
        output(i+1)  =  prefix + "," + timestrs(0) + "," \
                                                 + timestrs(i) + ","\
                                                 + sprintf("%0.1f", series@height) + ","\
                                                 + sprintf("%0.2f", series(i))
                                                 
    end do
    asciiwrite(fname, output)

end





;******************************************************
; Read locations from file with named columns
;******************************************************
undef("read_locations")
procedure read_locations(loc_file)

begin
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
  name      = str_get_field(data, name_ind+1, ",")
 
  return (/loc_id, name, lat, lon/)
end
