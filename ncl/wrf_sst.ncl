
;   Example script to produce plots for a WRF real-data run,
;   with the ARW coordinate dynamics option.

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
begin
; The WRF ARW input file.  
; This needs to have a ".nc" appended, so just do it.
    
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
    
    type=ncl_out_type
    
    fname   = ncl_in_file
    a       = addfile(fname,"r")
    grid_id = a@GRID_ID
    d = grid_id

    diro     = ncl_out_dir
    web_dir = diro   
    print ("writing to "+web_dir)

    colors = (/"white","black","white","yellow","orange","DarkOrange",\
             "OrangeRed","Red1","Red2","Red4","DarkOrchid1","purple",\
             "MediumPurple3","Blue2","Blue4","DarkOliveGreen3"/)
    ; Set some basic resources
    res = True
    res@MainTitle                   = "NOAA SST 1/12 degree"
    res@Footer  = False
    res@InitTime = True
    res@InitTime = True

    pltres = True
    pltres@PanelPlot = True
 
    mpres = True
    mpres@mpGeophysicalLineThicknessF = 2.0
    mpres@mpGeophysicalLineColor = "black"
    mpres@mpDataBaseVersion      = "Ncarg4_1"          ; higher res data base
    mpres@mpFillOn               = True
    mpres@mpFillDrawOrder        = "PostDraw"
    mpres@mpLandFillColor        = "DarkOliveGreen3"
    mpres@mpOceanFillColor       = -1
    mpres@mpInlandWaterFillColor = -1
    ;  mpres@mpDataBaseVersion  = "HighRes"

    if (a@GRID_ID .ge. 3) then
        mpres@mpDataBaseVersion  = "HighRes"
    end if

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

; What times and how many time steps are in the data set?
  times  = wrf_user_list_times(a)  ; get times in the file
  ntimes = dimsizes(times)         ; number of times in the file

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    i=0 ; only plot for initial time as sst is constant 
    res@TimeLabel = times(i)   ; Set Valid time to use on plots
    current_lead_hh=sprinti("%0.2i", i)
    print("Lead time is:"+current_lead_hh)
    fileout = web_dir+"/sst_d"+sprinti("%0.2i", grid_id)+".png"
    print("fileout is "+fileout)
    wks = gsn_open_wks(type,fileout)
    gsn_define_colormap(wks,"temp1")        
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; First get the variables we will need        

  sst = wrf_user_getvar(a,"SST",i)    ; slp
  ;sst@_FillValue = 0  
  wrf_smooth_2d( sst, 3 )              ; smooth slp

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


    ; Plotting options for SST                     
  opts = res         
  opts@cnFillOn = True  
  opts@cnLineColor = "Blue"
  opts@cnHighLabelsOn = True
  opts@cnLowLabelsOn = True
  opts@ContourParameters = (/ min(sst), max(sst), ((max(sst)-min(sst))/20) /)
  opts@gsnSpreadColors= True
  opts@cnLineLabelBackgroundColor = -1
  opts@gsnContourLineThicknessesScale = 2.0
  contour_psl = wrf_contour(a,wks,sst,opts)
  delete(opts)
;Text stuff
  gsres               = True
  gsres@gsMarkerIndex = 5          ; Use filled dots for markers.
  gsres@gsMarkerThicknessF = 3.5
  gsres@gsMarkerSizeF = 10.          ; polymarker size
  gsres@gsMarkerColor =  "red"
  gsres@gsFillBackgroundColor="1"

 textres              = True
 textres@txFontColor   = 1 ; referes to value in the current colormap
 textres@txFontHeightF = 0.015
 ns_offset              = 0.125

  plot = wrf_map_overlays(a,wks,(/contour_psl/),pltres,mpres)

  ;Thanet
  xxlat = 51.4625 ;-44. - 28./60. - 26./3600.
  xxlon = 1.633 ;-23. - 30./3600.

if (d.ge.2) then
    print("Plotting Thanet")
    print(xxlon+"  "+xxlat)
    hov = gsn_add_polymarker(wks,plot,xxlon,xxlat,gsres)
    txt = gsn_add_text(wks,plot,"Thanet",xxlon,xxlat-ns_offset,textres)
  end if

 ;Egmond aan Zee
  xxlat = 52.606 ;-44. - 28./60. - 26./3600.
  xxlon = 4.419 ;-23. - 30./3600.

if (d.ge.2) then
    print("Plotting Egmond an zee")
    print(xxlon+"  "+xxlat)
    egmond = gsn_add_polymarker(wks,plot,xxlon,xxlat,gsres)
    txt = gsn_add_text(wks,plot,"Egmond aan zee",xxlon,xxlat+ns_offset,textres)
end if



; Kentish Flat
  xxlat = 51. + 27./60 + 36/3600.
  xxlon = 1. + 5./60. + 24/3600.
  if (d.ge.3) then
    print("Plotting Kentish flats")
    print(xxlon+"  "+xxlat)
     ris = gsn_add_polymarker(wks,plot,xxlon,xxlat,gsres)
     txt = gsn_add_text(wks,plot,"Kentish Flats",xxlon,xxlat+ns_offset,textres)
  end if


 ; East Anglia 1
   xxlat = 52.234
   xxlon = 2.2478



 if (d.ge.2) then
    print("Plotting East Anglia 1")
    print(xxlon+"  "+xxlat)
    eaone = gsn_add_polymarker(wks,plot,xxlon+0.02,xxlat,gsres)
    eaonetxt = gsn_add_text(wks,plot,"East Anglia 1",xxlon,xxlat-ns_offset,textres)
end if

; Dan tysk
  xxlat = 55. + 8./60 + 24/3600.
  xxlon = 7. + 12./60. + 0/3600.

if (d.ge.2) then
    print("Plotting DanTysk")
    print(xxlon+"  "+xxlat)
    nys = gsn_add_polymarker(wks,plot,xxlon,xxlat,gsres)
    txt = gsn_add_text(wks,plot,"DanTysk",xxlon,xxlat+ns_offset,textres)
end if
    print("before draw")
	draw(plot) 
	frame(wks) 

end
