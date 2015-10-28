;*******************************************************************
;   Example script to produce dbz plots for a WRF real-data run,
;   with the ARW coordinate dynamics option.
;   November 2008
;******************************************************************
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"


;******************************************************
; Fetch some settings from environment variables
;******************************************************
  fcst_file               = getenv("FCST_FILE")
  domain_dir              = getenv("DOMAIN_DIR")
  out_dir	                = getenv("NCL_OUT_DIR")
  type                    = getenv("NCL_OUTPUT")
  loc_file                = getenv("LOCATIONS_FILE")
 
;******************************************************
; Manually override options for testing
;******************************************************
  ;fcst_file               = "/home/slha/domains/gfs_3km/ABB/wrfout_d01_2007-08-22_12:00:00.nc"
  ;out_dir                 = "/home/slha/domains/gfs_3km/ABA/plots"
  ;domain_dir              = getenv("DOMAIN_DIR")
  ;out_dir 				  = getenv("NCL_OUT_DIR")
  ;type                    = "png"


;******************************************************
; Read in locations from text file
;******************************************************
  loc_data = asciiread(loc_file,-1,"string")
  loc_ids = str_get_field(loc_data,1,",")
  loc_names = str_get_field(loc_data,2,",")
  loc_lats  = str_to_float(str_get_field(loc_data,3,",")
  loc_lons = str_to_float(str_get_field(loc_data,4,",")
  print(loc_names)

  ;station_names = (/"fino", "gabbard", "lilligrund"/) 
  ;station_lats  = (/54.01386,51.94, 55.488922/)
  ;station_lons  = (/6.5865, 1.92, 12.7865/)
  ;nstations     = dimsizes(station_names)
  ;print(nstations)





;******************************************************
; Add WRF ARW input file.  
;******************************************************
 a = addfile(fcst_file,"r")


;******************************************************
; Set some basic resources
;******************************************************
  res = True
  res@MainTitle                   = "REAL-TIME WRF"

  pltres = True
  mpres = True

;******************************************************
; Times and dimensions
;******************************************************
; Which times and how many time steps are in the data set?
  times = wrf_user_getvar(a,"times",-1)  ; get all times in the file
  ntimes = dimsizes(times)         ; number of times in the file

;******************************************************
; Loop through times
;******************************************************

  do it = 1,ntimes-1               ; TIME LOOP
 
     print("Working on time: " + times(it) )

    ;******************************************************
    ; Workstation
    ;******************************************************
    
    wks = gsn_open_wks(type,out_dir+"/radar_"+ times(it))
    gsn_define_colormap(wks,"WhViBlGrYeOrReWh")


     res@TimeLabel = times(it)   ; Set Valid time to use on plots


    ; First get the variables we will need        
    ; Both dbz and mdbz will be calculated using constant intercept parameters
    ; (as in early Reisner-2), with values of 8x10^6, 2x10^7, and 4x10^6 m^-4,
    ; for rain, snow, and graupel, respectively.

     mdbz = wrf_user_getvar(a,"mdbz",it) 
     ;dbz = wrf_user_getvar(a,"dbz",it) 

     opts = res                         
     opts@cnFillOn = True  
     opts@ContourParameters = (/ 5., 75., 5./)
     ;contour = wrf_contour(a,wks,dbz(1,:,:),opts)     ; plot only lowest level
     ;plot = wrf_map_overlays(a,wks,(/contour/),pltres,mpres)
 
     contour = wrf_contour(a,wks,mdbz,opts)
     plot = wrf_map_overlays(a,wks,(/contour/),pltres,mpres)
 

   end do        ; END OF TIME LOOP
