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
  fcst_file    = getenv("FCST_FILE")
  domain       = getenv("NEST_ID")
  out_dir      = getenv("NCL_OUT_DIR")
  type         = getenv("NCL_OUT_TYPE")
  prefix       = "radar"

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

  mpres@mpGeophysicalLineThicknessF = 2.0
  mpres@mpGeophysicalLineColor = "black"
  mpres@mpDataBaseVersion      = "Ncarg4_1"          ; higher res data base
  mpres@mpFillOn               = True
  mpres@mpFillDrawOrder        = "PreDraw"
  mpres@mpLandFillColor        = "DarkOliveGreen3"
  mpres@mpOceanFillColor       = -1
  mpres@mpInlandWaterFillColor = -1

*****************************************************
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
    current_lead_hh=sprinti("%0.2i", it)
    
    ;******************************************************
    ; Create workstation
    ;******************************************************
    wks = gsn_open_wks(type,out_dir+"/radar_d"+domain+"_"+current_lead_hh)
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
