
;   Example script to produce plots for a WRF real-data run,
;   with the ARW coordinate dynamics option.

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
; load the wrf2geotiff library from the VAPOR distribution:
load "$VAPOR_ROOT/share/examples/NCL/wrf2geotiff.ncl"


begin
; The WRF ARW input file.  
; This needs to have a ".nc" appended, so just do it.
    
;**************************************************************
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
    
    type="oldps"         ; must be oldps for vapor
    
    prefix        = "sst_ol"
    labelbar      = "sst_ol_labelbar"      ; name of the labelbar file
    labelbar_type = "png"
    
    fname   = ncl_in_file
    a       = addfile(fname,"r")
    grid_id = a@GRID_ID
    d = grid_id

    diro     = ncl_out_dir

    ;colors = (/"white","black","white","yellow","orange","DarkOrange",\
    ;         "OrangeRed","Red1","Red2","Red4","DarkOrchid1","purple",\
    ;         "MediumPurple3","Blue2","Blue4","DarkOliveGreen3"/)

         
    ;****************************************
    ; colormaps quite confusing
    ; first is background colour
    ; second is foreground (?) lines etc
    ; last is often used for land filling
    ; rest are for contouring
    ;****************************************
    wks = gsn_open_wks("oldps","dummy")
    gsn_define_colormap(wks,"hotcold_18lev")
    colors = gsn_retrieve_colormap(wks)
    print(colors)
    delete(wks)
    
    dims = dimsizes(colors)
    clen = dims(0)
    print(clen)
    ;contour_col = colors(2:clen-2)
    ;print(contour_col)
    contour_clen = clen-3  

    
    ; Set some basic resources
    res = True
    res@MainTitle                   = "SST"
    res@Footer  = False
    res@InitTime = True
    res@InitTime = True

    pltres = True
    pltres@gsnFrame = False
 
    mpres = True
    mpres@mpOutlineBoundarySets = "NoBoundaries"
    mpres@mpGridAndLimbOn = False

    mpres@mpGeophysicalLineThicknessF = 2.0
    mpres@mpGeophysicalLineColor = "black"
    mpres@mpDataBaseVersion      = "Ncarg4_1"          ; higher res data base
    mpres@mpFillOn               = True
    mpres@mpFillDrawOrder        = "PostDraw"
    mpres@mpLandFillColor        = "Transparent"
    mpres@mpOceanFillColor       = -1
    mpres@mpInlandWaterFillColor = -1
    ;mpres@mpDataBaseVersion  = "HighRes"



;***************************************************************

; What times and how many time steps are in the data set?
  times  = wrf_user_list_times(a)  ; get times in the file
  ntimes = dimsizes(times)         ; number of times in the file

;***************************************************************

;    it=0 ; only plot for initial time as sst is constant 

do it=0, ntimes-1 ; Modified to do every time step to make animation easier
    print(it)
    ff = floattointeger(a->XTIME/60.)
    res@TimeLabel = times(it)   ; Set Valid time to use on plots
    current_lead_hh=sprinti("%0.2i", it)
    print("Lead time is:"+current_lead_hh)

    fileout = diro+"/"+prefix+"_d"+sprinti("%0.2i",grid_id)+"_"+sprinti("%0.2i",ff(it))

    wks = gsn_open_wks(type,fileout)
    gsn_define_colormap(wks, colors)     

    ; wrf2geotiff_open() creates the opaque pointer wrf2gtiff:
    wrf2gtiff = wrf2geotiff_open(wks)

    
    
;***************************************************************
; First get the variables we will need        

  sst = wrf_user_getvar(a,"SST",it)  -272.15; SST in C
  ;wrf_smooth_2d(sst, 3 )              ; smooth sst

  landmask = wrf_user_getvar(a, "LANDMASK", it)   ; landmask, 1=land
  sst_ocean = mask(sst,landmask,0)
  ;sst@units = "C"
  ;sst@_FillValue = 0  

;***************************************************************


    ; Plotting options for SST                     
    opts                                 = res         
    opts@cnFillOn                        = True  
    opts@cnLineColor                     = "Blue"
    opts@cnHighLabelsOn                  = True
    opts@cnLowLabelsOn                   = True
    opts@cnFillDrawOrder                 = "PreDraw"
    opts@cnFillMode                      = "Raster"
    opts@gsnSpreadColors                 = True
    opts@cnLineLabelBackgroundColor      = -1
    opts@gsnContourLineThicknessesScale = 2.0

    ;***************************************
    ; Since we are making a seperate labelbar
    ; we need close control over the plot 
    ; parameters. 
    ;***************************************
    contour_step   = 2.0
    raw_min        = floattointeger(floor(min(sst)))
    raw_max        = floattointeger(ceil(max(sst)))
    contour_min    = raw_min - mod(raw_min, contour_step)
    contour_max    = raw_max - mod(raw_max, contour_step) + contour_step
    contour_num    = floattointeger((contour_max - contour_min)/ contour_step) + 1
    print(contour_min)
    print(contour_max)
    print(contour_num)
    contour_values = fspan(contour_min, contour_max, contour_num)
    print(contour_values)
    
    opts@cnLevelSelectionMode = "ManualLevels"	; manually set the contour levels with the following 3 resources
    opts@cnMinLevelValF  = contour_min			; set the minimum contour level
    opts@cnMaxLevelValF  = contour_max      	; set the maximum contour level
    opts@cnLevelSpacingF = contour_step			; set the interval between contours
    
    
    contour_sst = wrf_contour(a,wks,sst_ocean,opts)
    delete(opts)

    plot = wrf_map_overlays(a,wks,(/contour_sst/),pltres,mpres)

    wrf2geotiff_write(wrf2gtiff, a, times(it), wks, plot, True)
    ; The frame is needed between time steps after the wrf2geotiff_write
    frame(wks)
    wrf2geotiff_close(wrf2gtiff,wks)
    delete(wks)
    delete(wrf2gtiff)
end do

    ;*************************************************************************
    ; Try and create a matching label bar
    ;*************************************************************************
    lbname = diro+"/"+labelbar
    wks  = gsn_open_wks(labelbar_type,lbname)
    gsn_define_colormap(wks,colors)
    
    nboxes = contour_num                ; # of labelbar boxes
    stride = contour_clen / nboxes
    print(contour_clen)
    print(nboxes)
    print(stride)
    fill_colors = ispan(2,clen-1,stride)

    lblabels    = sprintf("%6.1f", contour_values)
    print(lblabels)
    lbres                           = True
    lbres@gsnMaximize               = True
    lbres@lbAutoManage              = False         ; we control label bar
    lbres@lbFillColors              = fill_colors   ; use nice strided colors  
    lbres@lbPerimOn                 = False         ; Turn off labelbar perimeter.
    lbres@lbMonoFillPattern         = True          ; one pattern, all solid
    lbres@pmLabelBarHeightF         = 0.3           ; default 0.6
    lbres@pmLabelBarWidthF          = 0.09          ; 0.15 default
    gsn_labelbar_ndc(wks,nboxes,lblabels,0.2,0.8,lbres)
    frame(wks)
    draw(wks)
    cmd="convert -trim " + lbname +" "+lbname
    system(cmd)

end
