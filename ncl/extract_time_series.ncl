;******************************************************
; Extract time-series from WRF netcdf files 
; write output to a simple text file
; Which variables are extracted are hard coded
; in this script, starting at around line
;******************************************************

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRF_contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/time_axis_labels.ncl"
load "$HOME/code/wrftools/trunk/ncl/wrftools.ncl"


begin

;******************************************************
; Constants / hard coded options
;******************************************************
  radians_per_degree = 0.0174532925
  extract_heights    = (/50.,60.,70.,80.,90.,100./)
  dims    = dimsizes(extract_heights)
  nlevels = dims(0)
  delete(dims)

;  max_level          = 6   ; used to limit the number 
;                           ; of vertical levels read


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
; Horizontal interpolation options
; 0: none, use grid cell value
; 1: bilinear interpolation
;******************************************************
  interp_option = 0

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
  name      = str_get_field(data, name_ind+1, ",")

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
 ; Get times from file
 ;******************************************************
  times     = f->Times
  fcst_hrs  = WRF_Times_to_udunits(times, 0)    ; using 0 forces the units to be hours since first time in the file
  init_time = chartostring(times(0,0:12))

 ;******************************************************
 ; Get coordinates
 ;******************************************************

  lat2d  = f->XLAT(0,:,:)
  lon2d  = f->XLONG(0,:,:)

  dims   = dimsizes(times)
  ntimes = dims(0)
  tstart = times(0,:)            ;   use the WRF forecast to specify the 
  tend   = times(ntimes-1, :)    ;   start   and end points
  delete(dims)


;******************************************************
; File naming, headers
;
; To be consistent with existing code, files should be 
; named like: SLG_VGRD_d01_100_2012-11-17_12.txt
; where: SLG  = location_id
;          VGRD = 'standard' variable name
;          d01  = nest_id
;          100  = height above surface
; 2012-11-17_12 = fcst initial time  
;******************************************************

    header = (/"domain","model_run","model","nest_id","location_id","latitude","longitude","variable","init_time","valid_time","height","value"/)
    us = inttochar(95) ; underscore

;**********************************************************
; Level and terrain height
;**********************************************************

    ter           = wrf_user_getvar(f, "ter", 0)      ; assume terrain doesn't change with time
    hgt_amsl      = wrf_user_getvar(f, "z", -1)       ; height above sea level of model levels
                                                      ; this will be 4D, since height varies (slightly)

    new_hgt = conform(hgt_amsl, ter, (/2,3/))         ; ensure they terrain height is right dimensionality
    hgt_agl = hgt_amsl - new_hgt                      ; get the height of model levels above ground level


;************************************************************************
;  Wind speed and direction
;************************************************************************
    uvmet   = wrf_user_getvar(f, "uvmet", -1)     ; these are rotated, but are they unstaggered?
    u_tr_e  = uvmet(0,:,:,:,:)                   ; u_tr_e
    v_tr_e  = uvmet(1,:,:,:,:)                   ; v_tr_e
    u_agl   = wrf_user_intrp3d(u_tr_e, hgt_agl, "h", extract_heights,0, False) 
    v_agl   = wrf_user_intrp3d(v_tr_e, hgt_agl, "h", extract_heights,0, False) 
    ws_agl  = sqrt(u_agl*u_agl + v_agl*v_agl)     
    r2d     = 45.0/atan(1.0)                                       ;wd_e
    wd_agl  = atan2(u_agl, v_agl) * r2d + 180.


;************************************************************************
; Speed
;************************************************************************

    print("Processing wind speed")
    wrf_series              = rcm2points(lat2d, lon2d,  ws_agl, lat, lon, 0)
    wrf_series!0            = "time"
    wrf_series!1            = "height"
    wrf_series!2            = "loc"
    wrf_series&time         = fcst_hrs
    wrf_series&height       = extract_heights


    ;********************************************************
    ; Attach metadata
    ;********************************************************
    wrf_series@domain       = domain
    wrf_series@model        = "WRF"
    wrf_series@model_run    = model_run
    wrf_series@nest_id      = nest_id
    wrf_series@var_name     = "SPEED"    
    
    printVarSummary(wrf_series)

    do i=0,nlocs-1
        do j=0,nlevels-1
            series  = wrf_series(time|:, height|j, loc|i)
            series@loc_id = loc_id(i)
            series@lat    = lat(i)
            series@lon    = lon(i)
            printVarSummary(series)
            ihgt = floattoint(series@height)
            shgt = sprinti("%0.3i", ihgt)
            fname   = out_dir + "/" +\
                         series@loc_id + us +\
                         series@var_name + us + "d" +\
                         series@nest_id + us +\
                         shgt+ us +\
                         init_time +".txt"
            print(fname)
            write_series(series, fname)
            delete(series)
            delete(fname)
        end do
    end do
    delete(wrf_series)

;************************************************************************
; Direction. Direction can't realy be interpolated
; but we do it for now and hope for the best
;************************************************************************

    print("Processing wind direction")
    wrf_series              = rcm2points(lat2d, lon2d,  wd_agl, lat, lon, 0)
    wrf_series!0            = "time"
    wrf_series!1            = "height"
    wrf_series!2            = "loc"
    wrf_series&time         = fcst_hrs
    wrf_series&height       = extract_heights

    ;********************************************************
    ; Attach metadata
    ;********************************************************
    wrf_series@domain       = domain
    wrf_series@model        = "WRF"
    wrf_series@model_run    = model_run
    wrf_series@nest_id      = nest_id
    wrf_series@var_name     = "DIRECTION"    
    
    printVarSummary(wrf_series)

    do i=0,nlocs-1
        do j=0,nlevels-1
            series  = wrf_series(time|:, height|j, loc|i)
            series@loc_id = loc_id(i)
            series@lat    = lat(i)
            series@lon    = lon(i)
            printVarSummary(series)
            ihgt = floattoint(series@height)
            shgt = sprinti("%0.3i", ihgt)
            fname   = out_dir + "/" +\
                         series@loc_id + us +\
                         series@var_name + us + "d" +\
                         series@nest_id + us +\
                         shgt+ us +\
                         init_time +".txt"
            print(fname)
            write_series(series, fname)
            delete(series)
            delete(fname)
        end do
    end do
    delete(wrf_series)


;**********************************************************
; RAIN
;**********************************************************
   
    rain = f->RAINNC(:,:,:) + f->RAINC(:,:,:)
    wrf_series = rcm2points(lat2d, lon2d,  rain, lat, lon, 0)
    wrf_series@domain       = domain
    wrf_series@model        = "WRF"
    wrf_series@model_run    = model_run
    wrf_series@nest_id      = nest_id
    wrf_series@var_name     = "RAIN"    
    wrf_series@height       = 0.0
    wrf_series!0            = "time"
    wrf_series!1            = "loc"
    wrf_series&time         = fcst_hrs

    ; Convert to rain per hour 
    do n=1,ntimes-2
        k = ntimes-n
        wrf_series(k, :) = wrf_series(k,:)-wrf_series(k-1,:)
    end do

    printVarSummary(wrf_series)

    do i=0,nlocs-1
        series  = wrf_series(time|:, loc|i)
        series@loc_id = loc_id(i)
        series@lat    = lat(i)
        series@lon    = lon(i)
        printVarSummary(series)

        fname   = out_dir + "/" +\
                     series@loc_id + us +\
                     series@var_name + us + "d" +\
                     series@nest_id + us +\
                     "SFC"+ us +\
                     init_time +".txt"
        print(fname)
        write_series(series, fname)
        delete(series)
        delete(fname)
    end do
    delete(wrf_series)
    


    ;**********************************************************
    ; See level pressure
    ;**********************************************************
    ;slp = wrf_user_getvar(f,"slp",0)    ; slp

;**********************************************************
; T2
;**********************************************************
    print("processing T2")
    tc2 = wrf_user_getvar(f,"T2",-1)     ; T2 in Kelvin
    tc2 = tc2 - 273.16                   ; T2 in C
    tc2@units  = "C"
    
    wrf_series = rcm2points(lat2d, lon2d,  tc2, lat, lon, 0)
    wrf_series@domain       = domain
    wrf_series@model        = "WRF"
    wrf_series@model_run    = model_run
    wrf_series@nest_id      = nest_id
    wrf_series@var_name     = "T2"    
    wrf_series@height       = 2.0    
    wrf_series!0            = "time"
    wrf_series!1            = "loc"
    wrf_series&time         = fcst_hrs

    printVarSummary(wrf_series)

    do i=0,nlocs-1
        series  = wrf_series(time|:, loc|i)
        series@loc_id = loc_id(i)
        series@lat    = lat(i)
        series@lon    = lon(i)
        printVarSummary(series)
        ihgt = floattoint(series@height)
        shgt = sprinti("%0.3i", ihgt)
        fname   = out_dir + "/" +\
                     series@loc_id + us +\
                     series@var_name + us + "d" +\
                     series@nest_id + us +\
                     shgt+ us +\
                     init_time +".txt"
        print(fname)
        write_series(series, fname)
        delete(series)
        delete(fname)
    end do
    delete(wrf_series)


;**********************************************************
; TD2
;**********************************************************
    print("processing TD2")
    td2 = wrf_user_getvar(f,"td2",-1)    ; T2 in C
    td2@units  = "C"
    
    wrf_series = rcm2points(lat2d, lon2d,  td2, lat, lon, 0)
    wrf_series@domain       = domain
    wrf_series@model        = "WRF"
    wrf_series@model_run    = model_run
    wrf_series@nest_id      = nest_id
    wrf_series@var_name     = "TD2"    
    wrf_series@height       = 2.0    
    wrf_series!0            = "time"
    wrf_series!1            = "loc"
    wrf_series&time         = fcst_hrs

    printVarSummary(wrf_series)

    do i=0,nlocs-1
        series  = wrf_series(time|:, loc|i)
        series@loc_id = loc_id(i)
        series@lat    = lat(i)
        series@lon    = lon(i)
        printVarSummary(series)
        ihgt = floattoint(series@height)
        shgt = sprinti("%0.3i", ihgt)
        fname   = out_dir + "/" +\
                     series@loc_id + us +\
                     series@var_name + us + "d" +\
                     series@nest_id + us +\
                     shgt+ us +\
                     init_time +".txt"
        print(fname)
        write_series(series, fname)
        delete(series)
        delete(fname)
    end do
    delete(wrf_series)

exit


end

