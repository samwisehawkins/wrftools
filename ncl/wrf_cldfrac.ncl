;   Example script to produce plots for a WRF real-data run,
;   with the ARW coordinate dynamics option.

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
;gsn_define_colormap(wks,"wind_17lev")
begin


;************************************************************** 
; NCL expects some or all of the following to be defined on 
; the command-line
; ncl_in_file
; ncl_out_dir
; ncl_out_file
; ncl_out_type
; ncl_loc_file
; ncl_opt_file
;**************************************************************


;******************************************************
  
  ;******************************************************
  ; NCL expects some or all of the following to be defined on 
  ; the command-line
  ; ncl_in_file
  ; ncl_out_dir
  ; ncl_out_file
  ; ncl_out_ncl_out_type
  ; ncl_ncl_loc_file
  ; ncl_opt_file
  ;******************************************************
  load "$NCL_OPT_FILE"
  ncl_in_file = getenv("NCL_IN_FILE")
  ncl_out_dir = getenv("NCL_OUT_DIR")
  ncl_loc_file = getenv("NCL_LOC_FILE")
  ncl_out_type = getenv("NCL_OUT_TYPE")

  
  prefix   = "cloud"

  
  
  
;******************************************************
; Add the file
;***********************************************
  file_handle = addfile(ncl_in_file,"r")  
;
; The WRF ARW input file.  
;
  a = addfile(ncl_in_file,"r")
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
;do i=7,9
  print("Working on time: " + times(i) )
  res@TimeLabel = times(i)   ; Set Valid time to use on plots
    current_lead_hh=sprinti("%0.2i", i)
    print("Lead time is:"+current_lead_hh)
        fileout = ncl_out_dir + "/" + prefix + "_d" + domain + "_" + current_lead_hh 
        wks = gsn_open_wks(ncl_out_type,fileout)
        gsn_define_colormap(wks, colors)
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; First get the variables we will need        
  cldfra = wrf_user_getvar(a,"CLDFRA",i)    ; cloud fraction
  cldfra_avg = dim_avg_n_Wrap(cldfra, 2)
  cldfra_avg@description = "CLOUD FRACTION COLUMN AVG"
  cldfra_avg@units = "fraction"
  slp = wrf_user_getvar(a,"slp",i)          ; slp
  wrf_smooth_2d( slp, 3 )                   ; smooth slp
  u10 = wrf_user_getvar(a,"U10",i)          ; u at 10 m, mass point
  v10 = wrf_user_getvar(a,"V10",i)          ; v at 10 m, mass point
  wspd = sqrt(u10*u10+v10*v10)
  wspd@description = "Wind speed"
  wspd@units = "m/s"

 rain_exp = a->RAINNC(it,:,:)
 rain_con = a->RAINC(it,:,:)
 rain_exp = rain_exp - a->RAINNC(it-1,:,:)
 rain_con = rain_con - a->RAINC(it-1,:,:)
 rain_tot = rain_exp + rain_con

 # ensure a minimum cloud fraction if there is rainfall
 min_cldfra_avg = where(rain_tot>0.0001, 0.25, cldfra_avg)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

    ; Plotting options for wind speed
  opts = res                         
  opts@cnFillOn = True  

 gsn_define_colormap(wks,"wind_17lev")



 opts@ContourParameters = (/ 0., 1., 0.1/)
 opts@cnConstFEnableFill = True
 opts@cnFillPalette ="gsltod"
 opts@cnFillColors = (/0,2,3,4,11,14,17,20,21,22,23,23/)
 ;opts@cnFillColors = (/2,20,40,80,160,170,180,190,200,210,220,230,240,242,244,253/)
 
 ;opts@cnSpanFillPalette = True

  contour_w = wrf_contour(a,wks,min_cldfra_avg,opts)
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
  opts@NumVectors = 47           ; density of wind barbs
  vector = wrf_vector(a,wks,u10,v10,opts)
  delete(opts)
    

    ; MAKE PLOTS                                       
  plot = wrf_map_overlays(a,wks,(/contour_w,contour_psl/),pltres,mpres)

end do 
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
end
quit
