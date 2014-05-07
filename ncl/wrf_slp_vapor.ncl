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

  prefix = "slp_ol"

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
  pltres@gsnFrame = False

  pltres = True
  mpres = True
  ; Since these are for map overlays, don't draw boundaries or grid
  ; You probably want to draw these at first to check your data
  ; is projected correctly.
  mpres@mpOutlineBoundarySets = "NoBoundaries"
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
  
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

; What times and how many time steps are in the data set?
    FirstTime = True

    times  = wrf_user_list_times(a)  ; get times in the file
    ntimes = dimsizes(times)         ; number of times in the file

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

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

      res@TimeLabel = times(it)   ; Set Valid time to use on plots

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; First get the variables we will need        

    slp = wrf_user_getvar(a,"slp",it)  ; slp
    wrf_smooth_2d( slp, 3 )            ; smooth slp

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

; Don't skip the first time: we need an image at each time stamp
; This will result in a warning message on the first plot
;     if( .not. FirstTime ) then ; We don’t skip the first time

      ; Plotting options for Sea Level Pressure
        opts_psl = res          
        opts_psl@ContourParameters = (/ 900., 1100., 2. /)
        opts_psl@cnLineColor       = "Black"
        opts_psl@cnInfoLabelOn     = False
        opts_psl@cnLineLabelFontHeightF = 0.01
        opts_psl@cnLineLabelPerimOn = False
        opts_psl@cnLineThicknessF = 5.0     ; line thickness
        opts_psl@cnLineColor      = "Black"   ; color of contour lines
        ;opts_psl@gsnContourLineThicknessesScale = 2.5
        contour_psl = wrf_contour(a,wks,slp,opts_psl)
        delete(opts_psl)

        ; MAKE PLOTS                                       

        ; Total Precipitation 
        ; Don’t do this plot for geotiff:
        ;  plot = wrf_map_overlays(a,wks,contour_tot,pltres,mpres)

        ; Total Precipitation Tendency + SLP
        ; Do just this one plot:
        plot = wrf_map_overlays(a,wks,(/contour_psl/),pltres,mpres)

        ; Then put it in geotiff
        ; Do crop the image to the domain bounds
        wrf2geotiff_write(wrf2gtiff, a, times(it), wks, plot, True)
        ; The frame is needed between time steps after the wrf2geotiff_write
        frame(wks)
        wrf2geotiff_close(wrf2gtiff,wks)
        delete(wks)
        delete(wrf2gtiff)

;     end if    ; END IF FOR SKIPPING FIRST TIME

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

    end do        ; END OF TIME LOOP


; At the end, close the wrf2geotiff
; This is where the tiff writing takes place:
;  wrf2geotiff_close(wrf2gtiff,wks)

end
