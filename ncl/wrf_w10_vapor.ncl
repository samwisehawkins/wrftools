;   Example script to produce plots for a WRF real-data run,
;   with the ARW coordinate dynamics option.

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
load "$VAPOR_ROOT/share/examples/NCL/wrf2geotiff.ncl"
;gsn_define_colormap(wks,"wind_17lev")
begin

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
  type     = "oldps"             ; must be this for VAPOR plots
  diro     = ncl_out_dir
  loc_file = ncl_loc_file
  prefix   = "w10_ol"

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

  ;*****************************************************************
  ; Since they will be overlaid on top of OpenLayers maps,
  ; we don't want country outlines or borders, 
  ; although it is useful as a projection check
  ;*****************************************************************
  mpres@mpOutlineBoundarySets = "NoBoundaries"
  mpres@mpGridAndLimbOn = False
  ;mpres@mpGeophysicalLineThicknessF = 2.0
  ;mpres@mpGeophysicalLineColor = "black"
  ;mpres@mpDataBaseVersion      = "Ncarg4_1"          ; higher res data base
  ;mpres@mpFillOn               = True
  ;mpres@mpFillDrawOrder        = "PreDraw"
  ;mpres@mpLandFillColor        = "DarkOliveGreen3"
  ;mpres@mpOceanFillColor       = -1
  ;mpres@mpInlandWaterFillColor = -1

  if (a@GRID_ID .eq. 3) then
    mpres@mpDataBaseVersion  = "HighRes"
  end if

;***************************************************************
;***************************************************************

; What times and how many time steps are in the data set?
  times  = wrf_user_list_times(a)  ; get times in the file
  ntimes = dimsizes(times)         ; number of times in the file

;***************************************************************
do it=0,ntimes-1

  print("Working on time: " + times(it) )
  res@TimeLabel = times(it)   ; Set Valid time to use on plots
    current_lead_hh=sprinti("%0.2i", it)
    print("Lead time is:"+current_lead_hh)
    fileout = diro + "/" + prefix + "_d" + domain + "_" + current_lead_hh 
    wks = gsn_open_wks(type,fileout)
    gsn_define_colormap(wks, colors)
        
    ; wrf2geotiff_open() creates the opaque pointer wrf2gtiff:
    wrf2gtiff = wrf2geotiff_open(wks)

        
;***************************************************************
; First get the variables we will need        


    ;************************************************************
    ; Note, there appears to be a bug in wrf_user_getvar
    ; for U10 and V10, use the uvmet components instead
    ;u10 = wrf_user_getvar(a,"U10",it)    ; u at 10 m, mass point
    ;v10 = wrf_user_getvar(a,"V10",it)    ; v at 10 m, mass point
    ;************************************************************

    uvmet10 = wrf_user_getvar(a, "uvmet10", it)
    u10 = uvmet10(0, :, :)
    v10 = uvmet10(1, :, :)

    wspd = sqrt(u10*u10+v10*v10)
    wspd@description = "Wind speed"
    wspd@units = "m/s"

;***************************************************************
    
    ; Plotting options for Wind Vectors                 
    opts                            = res         
    opts@FieldTitle                 = "Wind"         ; overwrite Field Title
    opts@vcGlyphStyle               = "CurlyVector"  ; WindBard, CurlyVector, LineArrow, FillArrow
    opts@NumVectors                 = 20             ; density of wind barbs
    opts@vcLineArrowThicknessF      = 2.0            ; line arrow thickness 
    opts@vcWindBarbLineThickness    = 2.0            ; wind bar thickness
    vector = wrf_vector(a,wks,u10,v10,opts)
    delete(opts)
    

    ; MAKE PLOTS                                       
    plot = wrf_map_overlays(a,wks,(/vector/),pltres,mpres)

    ;**********************************************************
    ; VAPOR GeoTiff
    ;**********************************************************
    ; Do crop the image to the domain bounds
    wrf2geotiff_write(wrf2gtiff, a, times(it), wks, plot, True)
    ; The frame is needed between time steps after the wrf2geotiff_write
    frame(wks)
    wrf2geotiff_close(wrf2gtiff,wks)
    delete(wks)
    delete(wrf2gtiff)
    
    
end do 
;***************************************************************


end
