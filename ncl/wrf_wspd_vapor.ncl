;   Modified from the example script to produce plots for a WRF real-data run,
;   with the ARW coordinate dynamics option.

; From the "Using NCL with VAPOR to Visualize WRF-ARW data"
; tutorial.

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"

; load the wrf2geotiff library from the VAPOR distribution:
load "$VAPOR_ROOT/share/examples/NCL/wrf2geotiff.ncl"

begin
;
; The WRF ARW input file.  

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


  prefix = "wspd_ol"
  fcst_file = ncl_in_file
  a  = addfile(fcst_file,"r")
  grid_id = a@GRID_ID
  
; For wrf2geotiff, the type MUST be ps
; Actually - must be oldps, otherwise workstation 
; class comes out as Document

  type    = "oldps"
  diro    = ncl_out_dir


; Set some basic resources
  res = True
  res@MainTitle = "REAL-TIME WRF"

; Following are needed for control of frame advance:
  pltres = True
  mpres  = True
  pltres@gsnFrame = False


  ; Since these are for map overlays, don't draw boundaries or grid
  ; You probably want to draw these at first to check your data
  ; is projected correctly.
  ;mpres@mpFillOn               = True
  ;mpres@mpFillDrawOrder        = "PreDraw"
  ;mpres@mpLandFillColor        = "DarkOliveGreen3"
  
  ;mpres@mpOutlineBoundarySets = "NoBoundaries"
  mpres@mpGridAndLimbOn = False
  ;mpres@mpGeophysicalLineColor = "Black"
  ;mpres@mpNationalLineColor    = "Black"
  ;mpres@mpUSStateLineColor     = "Black"
  ;mpres@mpGridLineColor        = "Black"
  ;mpres@mpLimbLineColor        = "Black"
  ;mpres@mpPerimLineColor       = "Black"

  colors = (/"white","black","white","yellow","orange","DarkOrange",\
             "OrangeRed","Red1","Red2","Red4","DarkOrchid1","purple",\
             "MediumPurple3","Blue2","Blue4","DarkOliveGreen3"/)
  
;***************************************************************
;***************************************************************

; What times and how many time steps are in the data set?
    FirstTime = True

    times  = wrf_user_list_times(a)  ; get times in the file
    ntimes = dimsizes(times)         ; number of times in the file

;***************************************************************

; Loop over all the times, not just the odd times:
; do it = 0,ntimes-1,2 ; TIME LOOP
;    do it = 0, ntimes-1 ; Modified to do every time step

  do it = 0, ntimes-1 ; Modified to do every time step
    ;do it = 0, 2
    print("Working on time: " + times(it) )
    res@TimeLabel = times(it)   ; Set Valid time to use on plots
      
    ff = floattointeger(a->XTIME/60.)

    PlotName = diro+"/"+prefix+"_d"+sprinti("%0.2i",grid_id)+"_"+sprinti("%0.2i",ff(it))
    print("PlotName: "+PlotName)
    wks = gsn_open_wks(type,PlotName)
      

    gsn_define_colormap(wks, colors)  
    print("Working on time: " + times(it) )
      

    ; wrf2geotiff_open() creates the opaque pointer wrf2gtiff:
      wrf2gtiff = wrf2geotiff_open(wks)


      if (FirstTime) then            ; Save some times for tracking tendencies
        times_sav = times(it)
      end if
      res@TimeLabel = times(it)   ; Set Valid time to use on plots

;***************************************************************
; First get the variables we will need        
  ;u10 = wrf_user_getvar(a,"U10",it)    ; u at 10 m, mass point
  ;v10 = wrf_user_getvar(a,"V10",it)    ; v at 10 m, mass point
  uvmet10 = wrf_user_getvar(a, "uvmet10", it)
  u10 = uvmet10(0, :, :)
  v10 = uvmet10(1, :, :)
  
  wspd = sqrt(u10*u10+v10*v10)
  wspd@description = "Wind speed"
  wspd@units = "m/s"
;****************************************************************
  

    ;**********************************************************
    ; Plotting options for wind speed
    ;**********************************************************  
    opts = res                         
    opts@cnFillOn = True  
    
    

    gsn_define_colormap(wks,"wind_17lev")
    opts@ContourParameters = (/ 5., 23., 1./)
    opts@cnFillPalette = "wind_17lev"
    //opts@cnFillColors =(/2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23/) 
       

    contour_w = wrf_contour(a,wks,wspd,opts)
    delete(opts)

    ; MAKE PLOTS                                       

    ; Don’t do this plot for geotiff:
    ;  plot = wrf_map_overlays(a,wks,contour_tot,pltres,mpres)

    ; Do just this one plot:
    plot = wrf_map_overlays(a,wks,(/contour_w/),pltres,mpres)

    ; Then put it in geotiff
    ; Do crop the image to the domain bounds
    wrf2geotiff_write(wrf2gtiff, a, times(it), wks, plot, True)
    ; The frame is needed between time steps after the wrf2geotiff_write
    frame(wks)
    wrf2geotiff_close(wrf2gtiff,wks)
    delete(wks)
    delete(wrf2gtiff)



end do        ; END OF TIME LOOP
;***************************************************************

; At the end, close the wrf2geotiff
; This is where the tiff writing takes place:
;  wrf2geotiff_close(wrf2gtiff,wks)

end
