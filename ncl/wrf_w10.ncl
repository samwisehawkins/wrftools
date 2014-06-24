;   Example script to produce plots for a WRF real-data run,
;   with the ARW coordinate dynamics option.

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
;gsn_define_colormap(wks,"wind_17lev")
begin


;******************************************************

  print("\n\n**********************************************")
  print("wrf_precip.ncl")

;******************************************************

;******************************************************
; 
; NCL expects some or all of the following to be defined on 
; the command-line
; ncl_in_file
; ncl_out_dir
; ncl_out_file
; ncl_out_type
; ncl_loc_file
; ncl_opt_file
;**************************************************************

  File     = ncl_in_file
  type     = ncl_out_type
  diro     = ncl_out_dir
  loc_file = ncl_loc_file
  prefix   = "w10"

;******************************************************
; Add the file
;***********************************************
  file_handle = addfile(File,"r")  
;
; The WRF ARW input file.  
;
  a = addfile(File,"r")
  domain = sprinti("%0.2i",a@GRID_ID)

 colors = (/"white","black","white","yellow","orange","DarkOrange",\
             "OrangeRed","Red1","Red2","Red4","DarkOrchid1","purple",\
             "MediumPurple3","Blue2","Blue4","DarkOliveGreen3"/)

; Set some basic resources
  res = True
  res@MainTitle                   = "REAL-TIME WRF"
  res@Footer  = False
  res@InitTime = True
  res@InitTime = True
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

  if (a@GRID_ID .eq. 3) then
    mpres@mpDataBaseVersion  = "HighRes"
  end if

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

; What times and how many time steps are in the data set?
  times  = wrf_user_list_times(a)  ; get times in the file
  ntimes = dimsizes(times)         ; number of times in the file

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
do i=0,ntimes-1

  print("Working on time: " + times(i) )
  res@TimeLabel = times(i)   ; Set Valid time to use on plots
    current_lead_hh=sprinti("%0.2i", i)
    print("Lead time is:"+current_lead_hh)
        fileout = diro + "/" + prefix + "_d" + domain + "_" + current_lead_hh 
        wks = gsn_open_wks(type,fileout)
        gsn_define_colormap(wks, colors)
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; First get the variables we will need        

  slp = wrf_user_getvar(a,"slp",i)    ; slp
  wrf_smooth_2d( slp, 3 )              ; smooth slp
  u10 = wrf_user_getvar(a,"U10",i)    ; u at 10 m, mass point
  v10 = wrf_user_getvar(a,"V10",i)    ; v at 10 m, mass point
  wspd = sqrt(u10*u10+v10*v10)
  wspd@description = "Wind speed"
  wspd@units = "m/s"

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

    ; Plotting options for wind speed
    opts = res                         
    opts@cnFillOn = True  
    
    
    if  (a@GRID_ID .ge.3) then
        gsn_define_colormap(wks,"wind_17lev")
        opts@ContourParameters = (/ 5., 23., 1./)
        opts@cnFillColors =(/2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23/) 
    else
        opts@ContourParameters = (/ 5., 29., 3./)
        opts@cnFillColors = (/"transparent","yellow",\
                            "orange","DarkOrange",\
                            "OrangeRed","Red1","Red2","Red4","DarkOrchid1","purple",\
                            "MediumPurple3","Blue2","Blue4"/)
    end if
    contour_w = wrf_contour(a,wks,wspd,opts)
    delete(opts)

    ; Plotting options for SLP                     
    opts = res         
    opts@cnLineColor = "Blue"
    opts@cnHighLabelsOn = True
    opts@cnLowLabelsOn = True
    opts@ContourParameters = (/ 900., 1100., 4. /)
    opts@cnLineLabelBackgroundColor = -1
    opts@gsnContourLineThicknessesScale = 2.0
    contour_psl = wrf_contour(a,wks,slp,opts)
    delete(opts)
    
    ; Plotting options for Wind Vectors                 
    opts = res         
    opts@FieldTitle = "Wind"       ; overwrite Field Title
    ;opts@NumVectors = 47           ; density of wind barbs
    opts@vcMinDistanceF = 0.08      ; minimum distance between barbs
    vector = wrf_vector(a,wks,u10,v10,opts)
    delete(opts)
    

    ; MAKE PLOTS                                       
    plot = wrf_map_overlays(a,wks,(/contour_w,contour_psl,vector/),pltres,mpres)

end do 
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


end
