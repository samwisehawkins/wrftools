
;   Example script to produce plots for a WRF real-data run,
;   with the ARW coordinate dynamics option.

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"

begin
;
;******************************************************
; NCL expects some or all of the following to be defined on 
; the command-line
; ncl_in_file
; ncl_out_dir
; ncl_out_file
; ncl_out_type
; ncl_loc_file
; ncl_opt_file
;******************************************************
  fcst_file= ncl_in_file
  type     = ncl_out_type
  diro     = ncl_out_dir
  loc_file = ncl_loc_file
  prefix   = "t2"

;******************************************************
; Add the file
;***********************************************

  
  print("\n\n**********************************************")
  print("wrf_t2.ncl")

  
  
;******************************************************
; Add the file
;***********************************************

  a = addfile(fcst_file, "r")
  domain = sprinti("%0.2i",a@GRID_ID)

; Set some basic resources
  res = True
  res@gsnMaximize = True
  res@MainTitle                   = "REAL-TIME WRF"
  res@Footer = False
  res@InitTime = True 
  res@ValidTime= True
 
  pltres = True
  mpres = True
  mpres@mpGeophysicalLineThicknessF = 2.0
  mpres@mpGeophysicalLineColor = "black"
  mpres@mpDataBaseVersion     = "Ncarg4_1"          ; higher res data base
  if (a@GRID_ID .ge. 3) then
    mpres@mpDataBaseVersion  = "HighRes"
  end if


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

; What times and how many time steps are in the data set?
  times  = wrf_user_list_times(a)  ; get times in the file
  ntimes = dimsizes(times)         ; number of times in the file

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
first_time=1
last_lead_hh=sprinti("%0.2i", 0)

do it=0,ntimes-1
  current_lead_hh=sprinti("%0.2i", it)
  wks = gsn_open_wks(type,diro+"/"+prefix+"_d"+domain+"_"+current_lead_hh)
  gsn_define_colormap(wks,"WhViBlGrYeOrReWh")
  ;print("Working on time: " + times(it) )
  res@TimeLabel = times(it)   ; Set Valid time to use on plots


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; First get the variables we will need        

    slp = wrf_user_getvar(a,"slp",it)    ; slp
    wrf_smooth_2d( slp, 3 )              ; smooth slp
    tc2 = wrf_user_getvar(a,"T2",it)     ; T2 in Kelvin
    tc2 = tc2 - 273.16                   ; T2 in C
    tc2@units = "C"
    u10 = wrf_user_getvar(a,"U10",it)    ; u at 10 m, mass point
    v10 = wrf_user_getvar(a,"V10",it)    ; v at 10 m, mass point

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

    ; Plotting options for T                
    opts = res                         
    opts@cnFillOn = True  
    
    t_max = floattoint(ceil(max(tc2)))
    t_min = floattoint(floor(min(tc2)))
    t_start = t_min - (t_max % 5)
    t_end   = t_max + (t_max % 5)
    ;print(t_start)
    ;print(t_end)
    opts@ContourParameters = (/t_start,t_end,1/) ; winter 
    ;opts@ContourParameters = (/5.,30.,1/)  
    opts@gsnSpreadColorStart = 6
    opts@gsnSpreadColorEnd = 97
    contour_tc = wrf_contour(a,wks,tc2,opts)
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

    plot = wrf_map_overlays(a,wks,(/contour_tc,contour_psl,vector/),pltres,mpres)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
end do 
  
  print("wrf_t2.ncl")
  print("\n\n**********************************************")



end

