
;   Example script to produce plots for a WRF real-data run,
;   with the ARW coordinate dynamics option.
;   Plot SkewT's at a number of locations
;   Calculate ij posistions of all locations first.

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/skewt_func.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"

begin

;******************************************************
; Fetch some settings from environment variables
;******************************************************
  fcst_file               = getenv("FCST_FILE")
  loc_file                = getenv("LOCATIONS_FILE")
  out_dir                 = getenv("NCL_OUT_DIR")
  type                    = getenv("NCL_OUT_TYPE")
  nest_id                 = getenv("NEST_ID")
  prefix                  = "skewt"

;******************************************************
; Read locations from file 
;******************************************************
  cmd       = "sed  '/^[[:space:]]*#/d' " + loc_file          ; skip any commented lines
  lines     = systemfunc(cmd)
  header    = str_split(lines(0), ",")                        ; first line is header 
  data      = lines(1:)                                       ; rest is data

  loc_ind   = str_match_ind_ic(header, "location_id")         ; find which columns to get
  lat_ind   = str_match_ind_ic(header, "latitude")            
  lon_ind   = str_match_ind_ic(header, "longitude")
  name_ind  = str_match_ind_ic(header, "name")

  loc_id    = str_get_field(data, loc_ind+1, ",")                ; str_get_field numbering starts at 1
  lat       = stringtofloat(str_get_field(data, lat_ind+1, ",")) ; so add 1 to indices
  lon       = stringtofloat(str_get_field(data, lon_ind+1, ","))
  name      = str_get_field(data, name_ind+1, ",")
  nstations = dimsizes(name)


;******************************************************
; Add WRF ARW input file.  
;******************************************************
 a = addfile(fcst_file,"r")

;******************************************************
; Times and dimensions
;******************************************************

; What times and how many time steps are in the data set?
  FirstTime = True
  times  = wrf_user_list_times(a)  ; get times in the file
  ntimes = dimsizes(times)         ; number of times in the file

; Get some dimension info - so we can later check to make sure 
; the sounding locations are inside the model domain
  mdims = getfilevardimsizes(a,"P")
  nd = dimsizes(mdims)
  dimX = mdims(nd-1)
  dimY = mdims(nd-2)

;******************************************************
; Convert station locations to grid points
;******************************************************

; Get ij point in model domain for location "ip"
; loc(1) is south-north (y) and loc(0) is west-east (x)

  loc = wrf_user_ll_to_ij(a, lon, lat, True)

;******************************************************
; Loop through times
;******************************************************

  do it = 0,ntimes-1  ; TIME LOOP
  ;do it = 0,1        ; TIME LOOP
   
    print("Working on time: " + times(it) )

    tc  = wrf_user_getvar(a,"tc",it)         ; T in C
    td  = wrf_user_getvar(a,"td",it)         ; dew point temperature
    p   = wrf_user_getvar(a, "pressure",it)  ; grid point pressure
    z   = wrf_user_getvar(a, "z",it)         ; grid point height
    uvm = wrf_user_getvar(a,"uvmet",it)      ; umet and vmet averaged to mass points
     ; This is a 4D array where
     ; uvm(0,:,:,:) is umet, and
     ; uvm(1,:,:,:) is vmet, and
     ; This function rotate winds to earth coord.

    ; extract u and v from uvm array, and turn wind into kts
      u   = uvm(0,:,:,:)*1.94386 
      v   = uvm(1,:,:,:)*1.94386

   ;******************************************************
   ; Loop through stations 
   ;******************************************************

    do ip = 0, nstations-1,1    ; LOOP through above station locations and
                              ; plot a skewT if location is inside model domain
    
    print("Working on station: "+ name(ip))

   ;*****************************************************************
   ; Open workstation.
   ; Files should be named according to:
   ; skewt_d01_locn_fhr. 
   ; Where locn is location number (ie row number in location file)
   ; And fhr is forecast hour
   ;*****************************************************************
    fileout = out_dir + "/" + prefix + "_d" + nest_id + "_" + sprinti("%0.2i", ip+1) + "_" + sprinti("%0.2i", it+1)
    
    wks = gsn_open_wks(type,fileout)

    gsn_define_colormap(wks,"WhViBlGrYeOrReWh")
    locX = loc(0, ip)
    locY = loc(1, ip)

      if ( locX .lt. 1 .or. locX .gt. dimX .or. locY .lt. 1 .or. locY .gt. dimY )
         if ( FirstTime)
           print("Attempting to plot: " + "Station - " + name(ip) )
           print("                    " + "at location: "+ lat(ip) +" ; "+ stations_lons(ip) )
           print("                    " + "SKIP: Sounding outside model domain" )
         end if
      else

       ; We need array points in NCL space 
         locX = locX - 1
         locY = locY - 1

  ;      Define a few skew-T plotting options
         skewtOpts                   = True
         skewtOpts@DrawHeightScale   = True    ; plot height scale on side
         skewtOpts@DrawHeightScaleFt = False   ; plot height scale in km
         skewtOpts@DrawStandardAtm   = True    ; draw standard atm on plot
         skewtOpts@vpXF              = 0.12    ; controls off-set from left
         skewtOpts@vpYF              = 0.87    ; controls off-set from top
         skewtOpts@vpWidthF          = 0.75    ; controls size of plot
         skewtOpts@vpHeightF         = 0.75    ; controls size of plot
         skewtOpts@DrawFahrenheit    = False   ; use deg C scale
         skewtOpts@tiMainFontHeightF = 0.015   ; change height of main title
        ;skewtOpts@DrawColLine       = False   ; draw lines in black
         skewtOpts@DrawColAreaFill   = True    ; color on background plot
        ;skewtOpts@DrawColAreaColor  = "Green" ; final color may depend on the color table used
         skewtOpts@DrawColAreaColor  = 53      ; Light Green for WhViBlGrYeOrReWh color table
         skewtOpts@PrintOpts         = False   ; do not print options out


  ;      Get the skew-T background
         skewtOpts@tiMainString = name(ip)  + " at " + times(it)
         skewt_bkgd             = skewT_BackGround (wks, skewtOpts)
         draw (skewt_bkgd)


  ;      Draw the skew-T plot
         dataOpts           = True
         dataOpts@Parcel    = 1
         dataOpts@WspdWdir  = False  ; wind speed and dir [else: u,v]
         dataOpts@HspdHdir  = True   ; wind speed and dir [else: u,v]
         dataOpts@PlotWindH = False  ; plot wind barbs at h lvls [pibal; special]
         skewT_data = skewT_PlotData(wks, skewt_bkgd, p(:,locY,locX), \
                                                     tc(:,locY,locX), \
                                                     td(:,locY,locX), \
                                                      z(:,locY,locX), \
                                                      u(:,locY,locX), \
                                                      v(:,locY,locX), \
                                                     dataOpts)

  ;      Close the frame
         frame(wks)
        
         delete(skewtOpts)
         delete(dataOpts)
         delete(skewT_data)
         delete(skewt_bkgd)
         delete(wks)
      end if

   end do     ; END OF LOCATIONS

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

    FirstTime = False

  end do        ; END OF TIME LOOP

end
