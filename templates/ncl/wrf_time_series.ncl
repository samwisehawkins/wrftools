;   Example script to produce plots for a WRF real-data run,
;   with the ARW coordinate dynamics option.
;   Plot SkewT's at a number of locations

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"

begin

  radians_per_degree= 0.0175

;******************************************************
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
  File     = ncl_in_file
  type     = ncl_out_type
  diro     = ncl_out_dir
  loc_file = ncl_loc_file
;******************************************************

;******************************************************
; File naming
;******************************************************
  prefix   = "ts"

;******************************************************
; Add the file
;******************************************************

  file_handle = addfile(File,"r")
  domain = sprinti("%0.2i",file_handle@GRID_ID)


;******************************************************
; Set options
;******************************************************
  res = True
  res@InitTime= False
  res@ValidTime  = False
  res@gsnDraw  = False                          ; don't draw
  res@gsnFrame = False                          ; don't advance frame
  res@vpHeightF          = 0.3                  ; change aspect ratio of plot
  res@vpWidthF           = 0.9
  res@xyDashPattern = 0                        ; Make curves all solid

  res@pmLegendSide           = "Top"           ; Change location of 
  res@pmLegendParallelPosF   = .90             ; move units right
  res@pmLegendOrthogonalPosF = -0.52           ; more neg = down
  
  res@pmLegendWidthF         = 0.12            ; Change width and
  res@pmLegendHeightF        = 0.10            ; height of legend.
  res@lgLabelFontHeightF     = .015            ; change font height
  res@lgPerimOn              = False           ; no box around
; labels for the legend

  resP            = True                       ; modify the panel plot
  resP@gsnMaximize = True

; Get ij point in model domain for location "ip"
; loc(0) is south-north (y) and loc(1) is west-east (x)

  map_projection = file_handle@MAP_PROJ
  print("map_projection: "+map_projection)

  cone = 1.
  cen_lat  = file_handle@CEN_LAT
  if(isatt(file_handle,"STAND_LON")) then
    cen_long = file_handle@STAND_LON
  else
    cen_long = file_handle@CEN_LON
  end if
  true_lat1 = file_handle@TRUELAT1
  true_lat2 = file_handle@TRUELAT2
   
  if( map_projection .eq. 1) then    ; Lambert Conformal mapping
    if( (fabs(true_lat1 - true_lat2) .gt. 0.1) .and.  \
      (fabs(true_lat2 - 90. )      .gt. 0.1)       ) then
      cone = 10^(cos(true_lat1*radians_per_degree)) \
      -10^(cos(true_lat2*radians_per_degree))
      cone = cone/(10^(tan(45. -fabs(true_lat1/2.)*radians_per_degree)) - \
      10^(tan(45. -fabs(true_lat2/2.)*radians_per_degree))   )
    else
      cone = sin(fabs(true_lat1)*radians_per_degree)
    end if
  end if
  if(map_projection .eq. 2) then      ; polar stereographic
    cone = 1.
  end if
  if(map_projection .eq. 3) then      ; Mercator
    cone = 0.
  end if
  ;;print("Cone: "+cone)
  oe = "o~H-13V-2F22~/~V2H6~"


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


  rad  = 4.*atan(1.0)/180.


  Times = chartostring(file_handle->Times(:,8:12))
  print("times :"+Times)
  aux = file_handle->Times
  init_time = chartostring(file_handle->Times(0,0:15))

  day = stringtofloat(chartostring(aux(:,8:9)))
  hour = stringtofloat(chartostring(aux(:,11:12)))
  nn = dimsizes(day)
  x = ispan(0,nn-1,1)
  delete(aux)

  res@tmXBMode          = "Explicit"
  res@tmXBValues        = ispan(0,nn-1,12)
  res@tmXBLabels        = Times(::12)
  print(res@tmXBValues+"  "+res@tmXBLabels)

  res@trXMinF  = x(0)
  if (x(nn-1) .lt. 36.) then
    res@trXMaxF  = 36.
  else
    res@trXMaxF  = x(nn-1)
  end if

  ;;print(chartostring(aux)+"  "+x)

  ;**********************************************************
  ; Loop over locations
  ;**********************************************************

  do ip=0,dimsizes(lat)-1
    
    ;**********************************************************
    ; Open the workstation
    ;**********************************************************
    fileout = diro+"/" + prefix + "_"+ loc_id(ip) + "_d" + domain 
    
    wks = gsn_open_wks(type,fileout)

    loc = wrf_user_latlon_to_ij(file_handle, lat(ip), lon(ip))
    loc = loc - 1
    print("LOC: "+loc(0)+"  "+loc(1))
    print(lat(ip))
    print(lon(ip))

    var = file_handle->PH(0,0:4,:,:)
    PHB = file_handle->PHB(0,0:4,:,:)
    var = var + PHB
    z = wrf_user_unstagger(var,var@stagger)
    z = z/9.81 
    topo = file_handle->HGT(0,loc(0),loc(1))
    ;;print(z(:,loc(0),loc(1))-topo)
 
 
    t2 = file_handle->T2(:,loc(0),loc(1))
    t2 = t2 - 273.15
    print("t2:"+t2)

    PSFC = file_handle->PSFC(:,loc(0),loc(1))
    Q2   = file_handle->Q2(:,loc(0),loc(1))
  ;  td2  = wrf_td( PSFC,Q2)
     td2_all = wrf_user_getvar(file_handle,"td2",-1)	
     td2  = td2_all(:,loc(0),loc(1))
     rh_all =wrf_user_getvar(file_handle,"rh2",-1)
	rh2=rh_all(:,loc(0),loc(1))
	 print("t2:"+t2+" td2:"+td2+" RH:"+rh2)

   aux = file_handle->U(:,0:4,:,:)

    ua = wrf_user_unstagger(aux,aux@stagger)
    delete(aux)
    uu = ua(:,:,loc(0),loc(1))
    delete(ua)

    aux = file_handle->V(:,0:4,:,:)
    va = wrf_user_unstagger(aux,aux@stagger)
    delete(aux)
    vv = va(:,:,loc(0),loc(1))
    delete(va)
    wind = sqrt(uu*uu + vv*vv)

    alpha = (lon(ip) - cen_long)*cone*rad
    calpha = cos(alpha)
    salpha = sin(alpha)
    U = uu*calpha + vv*salpha
    V = vv*calpha - uu*salpha
    wdir = atan2(U,V)/rad+180.
    printVarSummary(wdir)
    delete(uu)
    delete(vv)
    delete(U)
    delete(V)

    u10 = file_handle->U10(:,loc(0),loc(1))
    v10 = file_handle->V10(:,loc(0),loc(1))
    wspd = sqrt(u10*u10 + v10*v10)

    U = u10*calpha + v10*salpha
    V = v10*calpha - u10*salpha
    wdir10 = atan2(U,V)/rad+180.
    delete(u10)
    delete(v10)
    delete(U)
    delete(V)
 
    rain = file_handle->RAINNC(:,loc(0),loc(1)) + file_handle->RAINC(:,loc(0),loc(1))

    do n=1,nn-2
      k = nn-n
      rain(k) = rain(k)-rain(k-1)
    end do

    fmt = "  %6.2f"
    print(sprintf(fmt,t2) + sprintf(fmt,td2) + sprintf(fmt,wspd) + \
          sprintf(fmt,wdir10)+ sprintf(fmt,rain))

    plot = new(4,graphic)                          ; create a plot array

    res@xyMarkLineMode         = "MarkLines"    ; Markers *and* lines
    res@xyMarkers              = (/6,11,16/)    ; 3 difile_handleerent markers
    res@xyLineColors           = (/"blue","red","green","purple"/)
    res@xyMarkerColors         = (/"blue","red","green","purple"/)
    res@tiYAxisString          = "wind speed (m/s)"
    res@pmLegendDisplayMode    = "Always"
    res@gsnRightString         = "Init time: "+init_time
    res@xyExplicitLegendLabels = (/" 10m"," 15m"," 55m"," 108m"/)

    res@trYMinF  = 0.0                   ; min value on y-axis
    plot(0) = gsn_csm_xy(wks,x,(/wspd,wind(:,0),wind(:,1),wind(:,2)/),res)

    res@tiYAxisString          = "wind direction (~F34~0~F~)"
    if (max((/wdir10,wdir(:,0),wdir(:,1),wdir(:,2)/)) .gt. 300.) then
      res@trYMaxF  = 360.0                   ; max value on y-axis
    end if
    delete(res@trYMinF)
    plot(1) = gsn_csm_xy(wks,x,(/wdir10,wdir(:,0),wdir(:,1),wdir(:,2)/),res)
    if (isatt(res, "trYMaxF")) then
      delete(res@trYMaxF)
    end if

    res@tiYAxisString          = "2-m T & Td (~F34~0~F~C)"
    delete(res@xyExplicitLegendLabels)
    res@pmLegendDisplayMode    = "Always"
    res@xyExplicitLegendLabels = (/" T2"," Td2"/)
    plot(2) = gsn_csm_xy(wks,x,(/t2(0:nn-1),td2(0:nn-1)/),res)

    res@trYMinF  = 0.0
    res@pmLegendDisplayMode    = "NoCreate"
    res@tiYAxisString          = "precipitation (mm/hour)"
    res@gsnYRefLine           = 0.              ; reference line   
    res@gsnXYBarChart         = True            ; create bar chart 
    res@gsnAboveYRefLineColor = "purple"           ; above ref line fill red
    res@xyMarkLineMode = "Lines"   
    res@trYMinF  = 0.0
    if (max(rain).lt.1.0) 
      res@trYMaxF  = 1.0
    end if
    plot(3) = gsn_csm_xy(wks,x-0.5,rain,res)
    if (isatt(res, "trYMaxF")) then
      delete(res@trYMaxF)
    end if

    res@gsnXYBarChart         = False
    delete(res@trYMinF)
    delete(res@gsnYRefLine)
    delete(res@gsnAboveYRefLineColor)
    delete(res@xyExplicitLegendLabels)

    resP@txString   = name(ip) 
    gsn_panel(wks,plot,(/4,1/),resP)               ; now draw as one plot

    delete(t2)
    delete(td2)
    delete(rain)
    delete(wind)
    delete(wspd)
    delete(PSFC)
    delete(Q2)
    ;succes=systemfunc("cp "+diro+"/plt* "+diro+"/pict000"+(ip+1)+".png")
    ;succes=systemfunc("rm -f "+diro+"/plt* ")
  end do
;updated = systemfunc("cp "+diro+"/*.png "+web_dir)
;clean = systemfunc("rm -f "+diro+"/*.png")
end

