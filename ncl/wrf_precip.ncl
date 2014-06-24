;   Example script to produce plots for a WRF real-data run,
;   with the ARW coordinate dynamics option.
;   In this example we first get the entire field over time, which will
;   make it easier to calculate tendencies
;
;   SH - modified to use a common interface for plotting NCL
;

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"

begin
  print("\n\n**********************************************")
  print("wrf_precip.ncl")

  ; NCL expects some or all of the following to be defined on 
  ; the command-line
  ; ncl_in_file
  ; ncl_out_dir
  ; ncl_out_file
  ; ncl_out_type
  ; ncl_loc_file
  ; ncl_opt_file
    
  if isdefined("ncl_opt_file") then 
    loadscript(opt_file)
  end if
    



  print("reading file "+ncl_in_file)
  a = addfile(ncl_in_file,"r")
  
  
  res = True
  res@MainTitle = "REAL-TIME WRF"
  res@Footer = False
  res@InitTime = True
  res@ValidTime= True

;  res@Footer = "False"
 
  pltres = True
  mpres = True
  mpres@mpGeophysicalLineColor = "Black"
  mpres@mpNationalLineColor    = "Black"
  mpres@mpUSStateLineColor     = "Black"
  mpres@mpGridLineColor        = "Black"
  mpres@mpLimbLineColor        = "Black"
  mpres@mpPerimLineColor       = "Black"
  mpres@mpFillOn               = True
  mpres@mpFillDrawOrder        = "PreDraw"
  mpres@mpLandFillColor        = "DarkOliveGreen3"
  mpres@mpOceanFillColor       = -1
  mpres@mpInlandWaterFillColor = -1

;********************************************
; What times and how many time steps are in the data set?
;********************************************
 
  Times  = wrf_user_list_times(a)  ; get times in the file
  ntimes = dimsizes(Times) 
  print(ntimes)
  mpres@mpDataBaseVersion     = "Ncarg4_1"          ; higher res data base
  if (a@GRID_ID .ge. 3) then
    mpres@mpDataBaseVersion  = "HighRes"
  end if

  do it = 1,ntimes-1

    ff = floattointeger(a->XTIME/60.)

    PlotName = ncl_out_dir+"/pp_d"+sprinti("%0.2i",a@GRID_ID)+"_"+sprinti("%0.2i",ff(it))
    print("PlotName: "+PlotName)
    wks = gsn_open_wks(ncl_out_type,PlotName)
    colors = (/"white","black","white","yellow","orange","DarkOrange",\
             "OrangeRed","Red1","Red2","Red4","DarkOrchid1","purple",\
             "MediumPurple3", "Violet","darkviolet","lightblue1", "Blue2","Blue4","DarkOliveGreen3"/)

    gsn_define_colormap(wks, colors)  
    print("Working on time: " + Times(it) )
    res@TimeLabel = Times(it)   ; Set Valid time to use on plots
;********************************************
; First get the variables we will need        

    slp = wrf_user_getvar(a,"slp",it)    ; slp
    wrf_smooth_2d( slp, 3 )            ; smooth slp

  ; Get non-convective, convective 
  ; Calculate total precipitation
    rain_exp = a->RAINNC(it,:,:)
    rain_con = a->RAINC(it,:,:)
    rain_exp = rain_exp - a->RAINNC(it-1,:,:)
    rain_con = rain_con - a->RAINC(it-1,:,:)
    rain_tot = rain_exp + rain_con
    rain_tot@description = "Total Precipitation"

; Plotting options for Sea Level Pressure
    opts_psl = res          
    opts_psl@ContourParameters = (/ 900., 1100., 2. /)
    opts_psl@cnLineColor       = "Blue"
    opts_psl@cnInfoLabelOn     = False
    opts_psl@cnLineLabelFontHeightF = 0.01
    opts_psl@cnLineLabelPerimOn = False
    opts_psl@gsnContourLineThicknessesScale = 1.5
    contour_psl = wrf_contour(a,wks,slp,opts_psl)
    delete(opts_psl)

   ; Plotting options for Precipitation
    opts_r = res                        
    opts_r@UnitLabel            = "mm"
    opts_r@cnLevelSelectionMode = "ExplicitLevels"
    opts_r@cnLevels             = (/ .1, .5, 1., 2., 3., 4., 5., 8., 10. /)
    opts_r@cnFillColors         = (/"transparent","Yellow","orange",\
                                   "DarkOrange",\
                                   "OrangeRed","Red1","Violet", "darkviolet", "lightblue1", "white"/)
    opts_r@cnInfoLabelOn        = False
    opts_r@cnConstFLabelOn      = False
    opts_r@cnFillOn             = True
   ; Precipitation Tendencies 
    opts_r@SubFieldTitle = "from " + Times(it-1) + " to " + Times(it)
    contour_tend = wrf_contour(a,wks, rain_tot,opts_r) ; total (color)
    delete(opts_r)

   ; MAKE PLOTS                                       

    plot = wrf_map_overlays(a,wks,(/contour_tend,contour_psl/),pltres,mpres)


  end do        ; END OF TIME LOOP

  print("wrf_precip.ncl")  
  print("\n\n**********************************************")


;********************************************

end
