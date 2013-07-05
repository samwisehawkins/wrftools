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
  nhgts = dims(0)
  delete(dims)

;******************************************************

;******************************************************
; Horizontal interpolation options
; 0: none, use grid cell value from wrf_user_ll_to_ij (not implemented yet!)
; 1: inverse distance weighting as implemented by rcm2points(opt=1)
; 2: bilinear interpolation as implemented by rcm2points(opt=2)
;******************************************************
  interp_option = 0


;******************************************************
; Output options
;******************************************************
  
  ;****************************
  ; 3D variables interpolated
  ; to height above surface
  ;****************************
  out3dAgl                   = True
  out3dAgl@u_tr              = False     ;earth relative u-component               - not yet implemented
  out3dAgl@v_tr              = False     ;earth relative v-component               - not yet implemented
  out3dAgl@speed             = True      ;wind speed                               - output as SPEED
  out3dAgl@direction         = True      ;earth-relative wind direction            - output as DIRECTION
  out3dAgl@t                 = True      ;temperature                              - output as T
  out3dAgl@theta             = True      ;potential temperature                    - output as THETA
  out3dAgl@tke_pbl           = True      ;TKE from PBL scheme                      - output as TKE (not yet implemented)

  
  ;****************************
  ; 2D (surface) variables
  ;****************************
  out2dMet                   = True
  out2dMet@sst               = True     ;sea-surface temperature                 - output as SST
  out2dMet@tsk               = False     ;skin (surface) temperature               - output as TSK
  out2dMet@t2                = True      ;temperature at 2m                        - output as T2
  out2dMet@td2               = True      ;dewpoint temperature at 2m               - output as TD2

  out2dMet@theta2            = False     ;potential temperature at 2m              - not yet implemented
  out2dMet@psfc              = False     ;pressure at the surface                  - not yet implemented
  out2dMet@slp               = False     ;sea-level pressure- using WRF-NCL        - not yet implemented
  out2dMet@tsfc              = False     ;temperature at the surface               - not yet implemented
  out2dMet@r_v_2m            = False     ;mixing ratio at 2m                       - not yet implemented
  out2dMet@q_2m              = False     ;specific humidity at 2m                  - not yet implemented
  out2dMet@rh_2m             = False     ;relative humidity at 2m                  - not yet implemented
  out2dMet@u_10m_gr          = False     ;u wind - grid - at 10m                   - not yet implemented
  out2dMet@v_10m_gr          = False     ;v wind - grid - at 10m                   - not yet implemented
  out2dMet@u_10m_tr          = False     ;u wind - rotated to earth- at 10m        - not yet implemented
  out2dMet@v_10m_tr          = False     ;v wind - rotated to earth - at 10m       - not yet implemented
  out2dMet@ws_10m            = False     ;wind speed - at 10m                      - not yet implemented
  out2dMet@wd_10m            = False     ;wind direction - earth - at 10m          - not yet implemented
  out2dMet@rain              = True      ;total grid scale precipitation           - output as RAIN
  out2dMet@precip_c          = False     ;total cumulus precipitation              - not yet implemented
  out2dMet@precip_fr         = False     ;fraction of frozen nonconv. precip       - not yet implemented
  out2dMet@dryairmass        = False     ;total dry air mass in column             - not yet implemented
  out2dMet@pblh              = False     ;PBL height                               - not yet implemented
  out2dMet@rho               = False     ;density at lowest eta level              - not yet implemented
  out2dMet@swdown            = True      ;downward short wave flux at ground surface -- output as SWDOWN
  out2dMet@cldfra_avg        = True      ;cloud fraction column average              -- output as CLDFRAAVG
  out2dMet@cldfra_max        = True      ;cloud fraction column maximun              -- output as CLDFRAMAX
;******************************************************

print(out2dMet)
print(out3dAgl)


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

  print("Read " + nlocs+ " locations from file: " + loc_file)

  ;******************************************************
  ; Get times and dimensions
  ;******************************************************
  lat2d =f->XLAT(0,:,:)
  lon2d =f->XLONG(0,:,:)
  
  ;times  = wrf_user_list_times(f)  ; get times in the file

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
 ; Get landmask for checking
 ;******************************************************
 landmask = f->LANDMASK(0,:,:)
 

 ;******************************************************
 ; Get grid indices of locations of interest
 ;******************************************************
  ij   = wrf_user_ll_to_ij(f,lon, lat, True)
  loc   = ij-1          ; To convert to NCL subscripts

  ;****************************************************
  ; Print location information
  ;****************************************************
  do n=0,nlocs-1
      print(loc_name(n) + " west_east: " + loc(0,n) + " south_north: " + loc(1,n) + " LANDMASK: " + landmask(loc(1,n), loc(0,n)))
  end do

;******************************************************
; File naming, headers
;
; To be consistent with existing code, files should be 
; named like: SLG_VGRD_d01_100_2012-11-17_12.txt
; where: SLG  = location_id
;          VGRD = 'standard' variable name
;          d01  = nest_id
;          100  = height above surface, integer 3-digits
; 2012-11-17_12 = fcst initial time  
;******************************************************

    header = (/"domain","model_run","model","nest_id","location_id","latitude","longitude","variable","init_time","valid_time","height","value"/)
    us = inttochar(95) ; underscore

;**********************************************************
; Level and terrain height
;**********************************************************

    ter           = wrf_user_getvar(f, "ter", 0)      ; assume terrain doesn't change with time
    hgt_amsl      = wrf_user_getvar(f, "z", -1)       ; height above sea level of model levels
                                                      ; this will be 4D, since height varies (slightly) hgt_amsl(time, level, y,x)
    new_hgt = conform(hgt_amsl, ter, (/2,3/))         ; ensure they terrain height is right dimensionality
    hgt_agl = hgt_amsl - new_hgt                      ; get the height of model levels above ground level
    dims = dimsizes(hgt_amsl)
    nlevels= dims(1)
    print(nlevels)
    delete(dims)

  

;************************************************************************
;  3D variables
;************************************************************************


    ;**********************************************
    ;  Wind speed and direction
    ;**********************************************
if (out3dAgl@speed) then

    uvmet   = wrf_user_getvar(f, "uvmet", -1)    ; these are rotated, but are they unstaggered?
    u_tr_e  = uvmet(0,:,:,:,:)                   ; u_tr_e
    v_tr_e  = uvmet(1,:,:,:,:)                   ; v_tr_e
    u_agl   = wrf_user_intrp3d(u_tr_e, hgt_agl, "h", extract_heights,0, False) 
    v_agl   = wrf_user_intrp3d(v_tr_e, hgt_agl, "h", extract_heights,0, False) 
    ws_agl  = sqrt(u_agl*u_agl + v_agl*v_agl)     
    r2d     = 45.0/atan(1.0)                                       ;wd_e
    wd_agl  = atan2(u_agl, v_agl) * r2d + 180.


    ;**********************************************
    ; Speed
    ;**********************************************
    print("Processing wind speed")
    var = ws_agl
    if (interp_option.eq.0)
        wrf_series = new((/ntimes,nhgts,nlocs/),"float")
        do i=0,nlocs-1
            wrf_series(:,:,i) = var(:, :,loc(1,i), loc(0,i))
        end do
    else
       wrf_series = rcm2points(lat2d, lon2d,  var, lat, lon, interp_option)
    end if
    delete(var)
    
    wrf_series!0            = "time"
    wrf_series!1            = "height"
    wrf_series!2            = "loc"
    wrf_series&time         = fcst_hrs
    wrf_series&height       = extract_heights

    ;*******************
    ; Attach metadata
    ;*******************
    wrf_series@domain       = domain
    wrf_series@model        = "WRF"
    wrf_series@model_run    = model_run
    wrf_series@nest_id      = nest_id
    wrf_series@var_name     = "SPEED"    
    

    do i=0,nlocs-1
        do k=0,nhgts-1
            series  = wrf_series(:, k, i)
            series@loc_id   = loc_id(i)
            series@loc_name = loc_name(i)
            series@lat    = lat(i)
            series@lon    = lon(i)
            ihgt = floattoint(series@height)
            shgt = sprinti("%0.3i", ihgt)
            fname   = out_dir + "/" +\
                         series@loc_id + us +\
                         series@var_name + us + "d" +\
                         series@nest_id + us +\
                         shgt+ us +\
                         init_time +".txt"
            write_series(series, fname)
            delete(series)
            delete(fname)
        end do
    end do
    delete(wrf_series)
end if


    ;**********************************************
    ; Direction. Direction can't really be 
    ; horizontally interpolated but we do it 
    ; anyway and hope for the best
    ;**********************************************
if (out3dAgl@direction) then
    print("Processing wind direction")

    var = wd_agl
    if (interp_option.eq.0)
        wrf_series = new((/ntimes,nhgts,nlocs/),"float")
        do i=0,nlocs-1
            wrf_series(:,:,i) = var(:, :,loc(1,i), loc(0,i))
        end do
    else
       wrf_series = rcm2points(lat2d, lon2d,  var, lat, lon, interp_option)
    end if
    delete(var)

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
    

    do i=0,nlocs-1
        do k=0,nhgts-1
            series  = wrf_series(:, k, i)
            series@loc_id = loc_id(i)
            series@loc_name = loc_name(i)
            series@lat    = lat(i)
            series@lon    = lon(i)
            ihgt = floattoint(series@height)
            shgt = sprinti("%0.3i", ihgt)
            fname   = out_dir + "/" +\
                         series@loc_id + us +\
                         series@var_name + us + "d" +\
                         series@nest_id + us +\
                         shgt+ us +\
                         init_time +".txt"
            ;print(fname)
            write_series(series, fname)
            delete(series)
            delete(fname)
        end do
    end do
    delete(wrf_series)
end if


    ;**********************************************
    ; T
    ;**********************************************
if(out3dAgl@t) then
    print("processing T")
    print("Waring. Check that temperature has been properly interpolated to heights above ground")
    t = wrf_user_getvar (f, "tc", -1)
    var   = wrf_user_intrp3d(t, hgt_agl, "h", extract_heights,0, False) 
    var@units  = "C"

    if (interp_option.eq.0)
        wrf_series = new((/ntimes,nhgts,nlocs/),"float")
        do i=0,nlocs-1
            wrf_series(:,:,i) = var(:, :,loc(1,i), loc(0,i))
        end do
    else
       wrf_series = rcm2points(lat2d, lon2d,  var, lat, lon, interp_option)
    end if
    delete(var)

    wrf_series@domain       = domain
    wrf_series@model        = "WRF"
    wrf_series@model_run    = model_run
    wrf_series@nest_id      = nest_id
    wrf_series@var_name     = "T"    
    wrf_series!0            = "time"
    wrf_series!1            = "height"
    wrf_series!2            = "loc"
    wrf_series&time         = fcst_hrs
    wrf_series&height       = extract_heights

    do i=0,nlocs-1
        do j=0,nhgts-1
            series  = wrf_series(:, j, i)
            series@loc_id = loc_id(i)
            series@loc_name = loc_name(i)
            series@lat    = lat(i)
            series@lon    = lon(i)
            ihgt = floattoint(series@height)
            shgt = sprinti("%0.3i", ihgt)
            fname   = out_dir + "/" +\
                     series@loc_id + us +\
                     series@var_name + us + "d" +\
                     series@nest_id + us +\
                     shgt+ us +\
                     init_time +".txt"
            write_series(series, fname)
            delete(series)
            delete(fname)
        end do
    end do
    delete(wrf_series)

end if


    ;**********************************************
    ; THETA
    ;**********************************************
if(out3dAgl@theta) then
    print("processing THETA")
    theta = wrf_user_getvar (f, "theta", -1)
    var   = wrf_user_intrp3d(theta, hgt_agl, "h", extract_heights,0, False) 
    var@units  = "C"

    if (interp_option.eq.0)
        wrf_series = new((/ntimes,nhgts,nlocs/),"float")
        do i=0,nlocs-1
            wrf_series(:,:,i) = var(:, :,loc(1,i), loc(0,i))
        end do
    else
       wrf_series = rcm2points(lat2d, lon2d,  var, lat, lon, interp_option)
    end if
    delete(var)
    wrf_series@domain       = domain
    wrf_series@model        = "WRF"
    wrf_series@model_run    = model_run
    wrf_series@nest_id      = nest_id
    wrf_series@var_name     = "THETA"    
    wrf_series!0            = "time"
    wrf_series!1            = "height"
    wrf_series!2            = "loc"
    wrf_series&time         = fcst_hrs
    wrf_series&height       = extract_heights

    do i=0,nlocs-1
        do j=0,nhgts-1
           series  = wrf_series(:,j, i)
            series@loc_id = loc_id(i)
            series@loc_name = loc_name(i)
            series@lat    = lat(i)
            series@lon    = lon(i)
            ihgt = floattoint(series@height)
            shgt = sprinti("%0.3i", ihgt)
            fname   = out_dir + "/" +\
                     series@loc_id + us +\
                     series@var_name + us + "d" +\
                     series@nest_id + us +\
                     shgt+ us +\
                     init_time +".txt"
            ;print(fname)
            write_series(series, fname)
            delete(series)
            delete(fname)
        end do
    end do
    delete(wrf_series)
    
end if

    ;**********************************************
    ; TKE
    ;**********************************************
if(out3dAgl@tke_pbl) then
    print("processing TKE")
    tke   = f->TKE_PBL(:,:,:,:)
    var   = wrf_user_intrp3d(tke, hgt_agl, "h", extract_heights,0, False) 
    var@units  = "m2 s-2"
    if (interp_option.eq.0)
        wrf_series = new((/ntimes,nhgts,nlocs/),"float")
        do i=0,nlocs-1
            wrf_series(:,:,i) = var(:, :,loc(1,i), loc(0,i))
        end do
    else
       wrf_series = rcm2points(lat2d, lon2d,  var, lat, lon, interp_option)
    end if

    delete(var)
    delete(tke)
    
    wrf_series@domain       = domain
    wrf_series@model        = "WRF"
    wrf_series@model_run    = model_run
    wrf_series@nest_id      = nest_id
    wrf_series@var_name     = "TKE"    
    wrf_series!0            = "time"
    wrf_series!1            = "height"
    wrf_series!2            = "loc"
    wrf_series&time         = fcst_hrs
    wrf_series&height       = extract_heights
    do i=0,nlocs-1
        do j=0,nhgts-1
           series  = wrf_series(:,j, i)
            series@loc_id = loc_id(i)
            series@loc_name = loc_name(i)
            series@lat    = lat(i)
            series@lon    = lon(i)
            ihgt = floattoint(series@height)
            shgt = sprinti("%0.3i", ihgt)
            fname   = out_dir + "/" +\
                     series@loc_id + us +\
                     series@var_name + us + "d" +\
                     series@nest_id + us +\
                     shgt+ us +\
                     init_time +".txt"
            write_series(series, fname)
            delete(series)
            delete(fname)
        end do
    end do
    delete(wrf_series)
end if

;************************************************************************
;  2D Surface Variables
;************************************************************************


    ;**********************************************
    ; RAIN
    ;**********************************************
if (out2dMet@rain) then
    print("Processing RAIN")
    var = f->RAINNC(:,:,:) + f->RAINC(:,:,:)

    if (interp_option.eq.0)
        wrf_series = new((/ntimes,nlocs/),"float")
        do i=0,nlocs-1
            wrf_series(:,i) = var(:, loc(1,i), loc(0,i))
        end do
    else
       wrf_series = rcm2points(lat2d, lon2d,  var, lat, lon, interp_option)
    end if
    delete(var)
    
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

    do i=0,nlocs-1
        series  = wrf_series(:, i)
        series@loc_id    = loc_id(i)
        series@loc_name  = loc_name(i)
        series@lat       = lat(i)
        series@lon       = lon(i)

        fname   = out_dir + "/" +\
                     series@loc_id + us +\
                     series@var_name + us + "d" +\
                     series@nest_id + us +\
                     "SFC"+ us +\
                     init_time +".txt"
        ;print(fname)
        write_series(series, fname)
        delete(series)
        delete(fname)
    end do
    delete(wrf_series)
end if    


    ;**********************************************
    ; T2
    ;**********************************************
if (out2dMet@t2) then
    print("processing T2")
    
    var = wrf_user_getvar(f,"T2",-1)- 273.15   ; T2 in C
    
    if (interp_option.eq.0)
        wrf_series = new((/ntimes,nlocs/),"float")
        do i=0,nlocs-1
            wrf_series(:,i) = var(:, loc(1,i), loc(0,i))
        end do
    else
       wrf_series = rcm2points(lat2d, lon2d,  var, lat, lon, interp_option)
    end if
    delete(var)    
    
    wrf_series@domain       = domain
    wrf_series@model        = "WRF"
    wrf_series@model_run    = model_run
    wrf_series@nest_id      = nest_id
    wrf_series@var_name     = "T2"    
    wrf_series@height       = 2.0    
    wrf_series!0            = "time"
    wrf_series!1            = "loc"
    wrf_series&time         = fcst_hrs
   

    
    do i=0,nlocs-1
        series        = wrf_series(:, i)
        series@loc_id = loc_id(i)
        series@loc_name = loc_name(i)
        series@lat    = lat(i)
        series@lon    = lon(i)
        ihgt = floattoint(series@height)
        shgt = sprinti("%0.3i", ihgt)
        fname   = out_dir + "/" +\
                     series@loc_id + us +\
                     series@var_name + us + "d" +\
                     series@nest_id + us +\
                     shgt+ us +\
                     init_time +".txt"
        write_series(series, fname)
        delete(series)
        delete(fname)
    end do
    delete(wrf_series)
end if

    ;**********************************************
    ; TD2
    ;**********************************************
if (out2dMet@td2) then
    print("processing TD2")
    var = wrf_user_getvar(f,"td2",-1)    ; T2 in C
    var@units  = "C"
    
    if (interp_option.eq.0)
        wrf_series = new((/ntimes,nlocs/),"float")
        do i=0,nlocs-1
            wrf_series(:,i) = var(:, loc(1,i), loc(0,i))
        end do
    else
       wrf_series = rcm2points(lat2d, lon2d,  var, lat, lon, interp_option)
    end if
    delete(var)
    
    wrf_series@domain       = domain
    wrf_series@model        = "WRF"
    wrf_series@model_run    = model_run
    wrf_series@nest_id      = nest_id
    wrf_series@var_name     = "TD2"    
    wrf_series@height       = 2.0    
    wrf_series!0            = "time"
    wrf_series!1            = "loc"
    wrf_series&time         = fcst_hrs

    do i=0,nlocs-1
        series  = wrf_series(:,i)
        series@loc_id = loc_id(i)
        series@loc_name = loc_name(i)
        series@lat    = lat(i)
        series@lon    = lon(i)
        ihgt = floattoint(series@height)
        shgt = sprinti("%0.3i", ihgt)
        fname   = out_dir + "/" +\
                     series@loc_id + us +\
                     series@var_name + us + "d" +\
                     series@nest_id + us +\
                     shgt+ us +\
                     init_time +".txt"

        write_series(series, fname)
        delete(series)
        delete(fname)
    end do
    delete(wrf_series)
end if

    ;**********************************************
    ; SST
    ;**********************************************
if (out2dMet@sst) then
    print("processing SST")
    var = f->SST(:,:,:)-273.15
    var@units  = "C"
    if (interp_option.eq.0)
        wrf_series = new((/ntimes,nlocs/),"float")
        do i=0,nlocs-1
            wrf_series(:,i) = var(:, loc(1,i), loc(0,i))
        end do
    else
       wrf_series = rcm2points(lat2d, lon2d,  var, lat, lon, interp_option)
    end if
    delete(var)


    wrf_series@domain       = domain
    wrf_series@model        = "WRF"
    wrf_series@model_run    = model_run
    wrf_series@nest_id      = nest_id
    wrf_series@var_name     = "SST"    
    wrf_series@height       = 0    
    wrf_series!0            = "time"
    wrf_series!1            = "loc"
    wrf_series&time         = fcst_hrs

;    printVarSummary(wrf_series)

    do i=0,nlocs-1
        series  = wrf_series(:, i)
        series@loc_id = loc_id(i)
        series@loc_name = loc_name(i)
        series@lat    = lat(i)
        series@lon    = lon(i)
        ihgt = floattoint(series@height)
        shgt = sprinti("%0.3i", ihgt)
        fname   = out_dir + "/" +\
                     series@loc_id + us +\
                     series@var_name + us + "d" +\
                     series@nest_id + us +\
                     shgt+ us +\
                     init_time +".txt"
        ;print(fname)
        write_series(series, fname)
        delete(series)
        delete(fname)
    end do
    delete(wrf_series)
end if
  


    ;**********************************************
    ; TSK
    ;**********************************************

if (  out2dMet@tsk) then
    print("processing TSK")
    var = f->TSK(:,:,:)-273.15
    var@units  = "C"
    if (interp_option.eq.0)
        wrf_series = new((/ntimes,nlocs/),"float")
        do i=0,nlocs-1
            wrf_series(:,i) = var(:, loc(1,i), loc(0,i))
        end do
    else
       wrf_series = rcm2points(lat2d, lon2d,  var, lat, lon, interp_option)
    end if
    delete(var)

    wrf_series@domain       = domain
    wrf_series@model        = "WRF"
    wrf_series@model_run    = model_run
    wrf_series@nest_id      = nest_id
    wrf_series@var_name     = "TSK"    
    wrf_series@height       = 0    
    wrf_series!0            = "time"
    wrf_series!1            = "loc"
    wrf_series&time         = fcst_hrs

    do i=0,nlocs-1
        series  = wrf_series(:, i)
        series@loc_id = loc_id(i)
        series@loc_name = loc_name(i)
        series@lat    = lat(i)
        series@lon    = lon(i)
        ihgt = floattoint(series@height)
        shgt = sprinti("%0.3i", ihgt)
        fname   = out_dir + "/" +\
                     series@loc_id + us +\
                     series@var_name + us + "d" +\
                     series@nest_id + us +\
                     shgt+ us +\
                     init_time +".txt"
        ;print(fname)
        write_series(series, fname)
        delete(series)
        delete(fname)
    end do
    delete(wrf_series)
end if





    ;**********************************************
    ; SWDOWN
    ;**********************************************
if (out2dMet@swdown) then
    print("processing SWDOWN")
    var = f->SWDOWN(:,:,:)
    if (interp_option.eq.0)
        wrf_series = new((/ntimes,nlocs/),"float")
        do i=0,nlocs-1
            wrf_series(:,i) = var(:, loc(1,i), loc(0,i))
        end do
    else
       wrf_series = rcm2points(lat2d, lon2d,  var, lat, lon, interp_option)
    end if
    delete(var)

    wrf_series@domain       = domain
    wrf_series@model        = "WRF"
    wrf_series@model_run    = model_run
    wrf_series@nest_id      = nest_id
    wrf_series@var_name     = "SWDOWN"    
    wrf_series@height       = 0    
    wrf_series!0            = "time"
    wrf_series!1            = "loc"
    wrf_series&time         = fcst_hrs

    do i=0,nlocs-1
        series  = wrf_series(:, i)
        series@loc_id = loc_id(i)
        series@loc_name = loc_name(i)
        series@lat    = lat(i)
        series@lon    = lon(i)
        ihgt = floattoint(series@height)
        shgt = sprinti("%0.3i", ihgt)
        fname   = out_dir + "/" +\
                     series@loc_id + us +\
                     series@var_name + us + "d" +\
                     series@nest_id + us +\
                     shgt+ us +\
                     init_time +".txt"
        write_series(series, fname)
        delete(series)
        delete(fname)
    end do
    delete(wrf_series)
end if

    ;**********************************************
    ; CLOUD FRACTION.
    ; This is computed in WRF on each model level
    ; What to do? Average? Maximum?
    ; Note that in WRF, threre is no feedback between
    ; sub-grid (paramterised cumulus) clouds, and
    ; SW downward radiation! See: 
    ;http://www.cmascenter.org/mwg-internal/de5fs23hu73ds/progress?id=DZMAIffR/q
    ;
    ; Currently take average over column!
    ;**********************************************

    ;**********************************************
    ; CLOUD FRACTION
    ;**********************************************
if (out2dMet@cldfra_avg) .or. (out2dMet@cldfra_max)
    print("processing CLDFRA")
    cldfra_eta = f->CLDFRA(:,:,:,:)

    cldfra_avg = dim_avg_n_Wrap(cldfra_eta, 1)
    cldfra_max = dim_max_n(cldfra_eta, 1)

    delete(cldfra_eta)
        
    ;*************************************
    ; CLOUD FRACTION AVG
    ;*************************************
    if (out2dMet@cldfra_avg)
        var=cldfra_avg
        if (interp_option.eq.0)
            wrf_series = new((/ntimes,nlocs/),"float")
            do i=0,nlocs-1
                wrf_series(:,i) = var(:, loc(1,i), loc(0,i))
            end do
        else
            wrf_series = rcm2points(lat2d, lon2d,  var, lat, lon, interp_option)
        end if
        delete(var)

        wrf_series@domain       = domain
        wrf_series@model        = "WRF"
        wrf_series@model_run    = model_run
        wrf_series@nest_id      = nest_id
        wrf_series@var_name     = "CLDFRAAVG"    
        wrf_series@height       = 0    
        wrf_series!0            = "time"
        wrf_series!1            = "loc"
        wrf_series&time         = fcst_hrs


        do i=0,nlocs-1
            series  = wrf_series(:, i)
            series@loc_id = loc_id(i)
            series@loc_name = loc_name(i)
            series@lat    = lat(i)
            series@lon    = lon(i)
            ihgt = floattoint(series@height)
            shgt = sprinti("%0.3i", ihgt)
            fname   = out_dir + "/" +\
                         series@loc_id + us +\
                         series@var_name + us + "d" +\
                         series@nest_id + us +\
                         shgt+ us +\
                         init_time +".txt"
            ;print(fname)
            write_series(series, fname)
            delete(series)
            delete(fname)
        end do
        delete(wrf_series)
        delete(cldfra_avg)
    end if    
    
    
    ;*************************************
    ; CLOUD FRACTION MAX
    ;*************************************
    if (out2dMet@cldfra_max)
        var=cldfra_max
        if (interp_option.eq.0)
            wrf_series = new((/ntimes,nlocs/),"float")
            do i=0,nlocs-1
                wrf_series(:,i) = var(:, loc(1,i), loc(0,i))
            end do
        else
            wrf_series = rcm2points(lat2d, lon2d,  var, lat, lon, interp_option)
        end if
        delete(var)

        wrf_series@domain       = domain
        wrf_series@model        = "WRF"
        wrf_series@model_run    = model_run
        wrf_series@nest_id      = nest_id
        wrf_series@var_name     = "CLDFRAMAX"    
        wrf_series@height       = 0    
        wrf_series!0            = "time"
        wrf_series!1            = "loc"
        wrf_series&time         = fcst_hrs
    
    ;    printVarSummary(wrf_series)
    
        do i=0,nlocs-1
            series  = wrf_series(:, i)
            series@loc_id = loc_id(i)
            series@loc_name = loc_name(i)
            series@lat    = lat(i)
            series@lon    = lon(i)
            ihgt = floattoint(series@height)
            shgt = sprinti("%0.3i", ihgt)
            fname   = out_dir + "/" +\
                         series@loc_id + us +\
                         series@var_name + us + "d" +\
                         series@nest_id + us +\
                         shgt+ us +\
                         init_time +".txt"
            ;print(fname)
            write_series(series, fname)
            delete(series)
            delete(fname)
        end do
        delete(wrf_series)
    delete(cldfra_max)
    end if
end if


    ;**********************************************
    ; PBLH
    ;**********************************************
if (out2dMet@pblh) then
    print("processing PBLH")
    var = f->PBLH(:,:,:)
    if (interp_option.eq.0)
       wrf_series = new((/ntimes,nlocs/),"float")
        do i=0,nlocs-1
            wrf_series(:,i) = var(:, loc(1,i), loc(0,i))
        end do
    else
        wrf_series = rcm2points(lat2d, lon2d,  var, lat, lon, interp_option)
    end if
    delete(var)

    wrf_series@domain       = domain
    wrf_series@model        = "WRF"
    wrf_series@model_run    = model_run
    wrf_series@nest_id      = nest_id
    wrf_series@var_name     = "PBLH"    
    wrf_series@height       = 0    
    wrf_series!0            = "time"
    wrf_series!1            = "loc"
    wrf_series&time         = fcst_hrs

;    printVarSummary(wrf_series)

    do i=0,nlocs-1
        series  = wrf_series(:, i)
        series@loc_id = loc_id(i)
        series@loc_name = loc_name(i)
        series@lat    = lat(i)
        series@lon    = lon(i)
        ihgt = floattoint(series@height)
        shgt = sprinti("%0.3i", ihgt)
        fname   = out_dir + "/" +\
                     series@loc_id + us +\
                     series@var_name + us + "d" +\
                     series@nest_id + us +\
                     shgt+ us +\
                     init_time +".txt"
        ;print(fname)
        write_series(series, fname)
        delete(series)
        delete(fname)
    end do
    delete(wrf_series)
    delete(pblh)
end if

  

print("*** SUCCESS NCL EXTRACT TIME SERIES ***")

end
