load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/ut_string.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl" 
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRF_contributed.ncl"



;******************************************************
; Read locations from file with named columns
;******************************************************
undef("read_locations")
function read_locations(loc_file)

begin
  cmd       = "sed  '/^[[:space:]]*#/d' " + loc_file          ; skip any commented lines
  lines     = systemfunc(cmd)                                 ; take input from sed
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
  
  ; NCL has bug where lists get reversed
  out    = [/loc_id, name, lat, lon/]
  ;out    = [/lon, lat, name, loc_id/]
  
  return(out)

end






;*****************************************************************************
; Horizontally interpolate to a set of locations
; interp_option: 0 nearest cell
;                1 inverse distance weighting as implemented by rcm2points(opt=1)
;                2 bilinear interpolation as implemented by rcm2points(opt=2)
;*****************************************************************************
undef("wrf_user_hinterp")
function wrf_user_hinterp(nc_file, var, lat, lon, xlat, xlong, interp_option)

begin
	dims   = dimsizes(var)
	ddims  = dimsizes(dims)
	ndims  = ddims(0)
	delete(ddims)
	
	ntimes = dims(0)
	nhgts  = dims(1)
	delete(dims)
    
	dims = dimsizes(lat)
	nlocs = dims(0)
	delete(dims)
	
	if (interp_option.eq.0)
	    
		;******************************************************
		; Get ij locations
		ij   = wrf_user_ll_to_ij(nc_file,lon, lat, True)
		loc  = ij-1          ; To convert to NCL subscripts
		;******************************************************
		if (ndims .eq. 4)
		    var_out = new((/nlocs, ntimes,nhgts/),"float")
		    do n=0,nlocs-1
			    var_out(n,:,:) = var(:,:,loc(1,n),loc(0,n))
			end do
	    end if
		if (ndims .eq. 3)
			var_out = new((/nlocs, ntimes/),"float")
		    do n=0,nlocs-1
			    var_out(n,:) = var(:,loc(1,n),loc(0,n))
			end do
	    end if
	else
        var_out = rcm2points(xlat, xlong,  var, lat, lon, interp_option)
    end if		
    var_out!0 = "location"
    
	; variable is no longer staggered if we have iterpolated to points
	;delete_VarAtts(var_out, (/"stagger", "coordinates"/))
	return(var_out)
end



;*******************************************************************************
;
; wrf_user_interp_vars
; Horizontally and vertically interpolates variables and new diagnostics 
; to a set of locations.
;
; Arguments:
; file_handle: wrfout files to extract from
; hgts: array of heights to extract to
; lat: array of latitudes to interpolate to
; lon: array of longitudes to interpoate to
; hgt: heights above model surface to iterpolate to
; time_in: which timestep to get, -1 gets all timesteps
; vars: object with attributes set which specify which variables to fetch. See below.
; opt: various options, currently
;      opt@h_interp: horizontal interpolation option
;      opt@rb_type: bulk richardson computation type
;
; TODO: TKE, RAIN, CLOUDFRAC
;*******************************************************************************

undef("wrf_user_interp_vars")
function wrf_user_interp_vars(file_handle, hgts[*]:numeric, lat[*]:numeric, lon[*]:numeric,time_in:integer, vars, opts)
local variable, time, var, u, v, u_in, v_in, pii, radians_per_degree, \
dims, nd, xlat, xlong, rank, \
R, g, cp, lv

begin
    ;******************************************************
    ; Constants / hard coded options
    ;******************************************************
    radians_per_degree = 0.0174532925
    R  = 287.058            ; gas constant for air
    g  = 9.81               ; gravitational acceleration
    cp = 1003.5             ; specific heat capacity of air
    lv = 2400000            ; latent heat of evaporation 
 
    print("wrf_user_interp_vars")
	print(hgts)
    ;******************************************************
    ; File handle
    ; nc_file gives us a single file
    ; file_handle[:] gives us all files
    ;******************************************************

    if(typeof(file_handle).eq."file") then
        ISFILE = True
        nc_file = file_handle
    else if(typeof(file_handle).eq."list") then
        ISFILE = False
        nc_file = file_handle[0]
	    ; note, we still need to use file_handle[:] to access all files
    else
        print("wrf_user_getvar: error: the first argument must be a file or a list of files opened with addfile or addfiles")
        return
    end if
    end if

    ;******************************************************
    ; Unpack input args so they are literals, not Variables
    time       = time_in(0)
    variables  = getvaratts(vars)
    print(variables)
    print(time)
    ;******************************************************

	
	;******************************************************
    ; Create lists to store the output variables and names
    out_vars  = NewList("fifo")
	out_names = NewList("fifo") ; may not be needed.
	;******************************************************
	
	;******************************************************
    ; Get some global attributes from file
    ;******************************************************
    nest_id = nc_file@GRID_ID
	

    ;******************************************************
    ; Latitudes, longitudes, times, dimension sizes
    ; Dimension sizes
    ;******************************************************
    dims    = dimsizes(hgts)
    nhgts   = dims(0)
    delete(dims)

    dims  = dimsizes(lat)
    nlocs = dims(0)
    delete(dims)
  

  
    xlat  = nc_file->XLAT(0,:,:) ; latitudes don't change over time
    xlong = nc_file->XLONG(0,:,:)
    times = nc_file->Times
    ud_times = wrf_times_c(times, 0)
	
	init_time = chartostring(times(0,0:12))

	; time of -1 gets all timesteps, otherwise we are feching one timestep
    dims = dimsizes(times)
    if (time .eq. -1) then 
        ntimes=dims(0)
    else ntimes=1
    end if
    delete(dims)
	
    
    dims = dimsizes(xlat)
    south_north = dims(0)
    west_east   = dims(1)
  
  
    ;******************************************************
    ; Get ij locations
    ij   = wrf_user_ll_to_ij(nc_file,lon, lat, True)
    loc  = ij-1          ; To convert to NCL subscripts
    ;******************************************************
  
  
    ;******************************************************
    ; Get basic variables we will need to derive
    ; additional diagnostics
    ; At some point implement a check here so we only fetch 
    ; what we need.
    ;******************************************************
 
	; always need terrain height, zeta level above sea level, zeta above ground level
	hgt_ter       = wrf_user_getvar(file_handle, "ter", 0)      ; assume terrain doesn't change with time
    hgt_amsl      = wrf_user_getvar(file_handle, "z", time)     ; height above sea level of model levels
                                                                ; this will be 4D, since height varies (slightly) hgt_amsl(time, level, y,x)

	hgt_new = conform(hgt_amsl, hgt_ter, (/2,3/))               ; ensure they terrain height is right dimensionality
    hgt_agl = hgt_amsl - hgt_new                                ; get the height of model levels above ground level
	
	hgt_agl_locs = wrf_user_hinterp(nc_file, hgt_agl, lat, lon, xlat, xlong, opts@interp_option)
	delete(hgt_new)

 
    if( any( (/vars@u, vars@v, vars@rib, vars@speed, vars@direction/) ) ) then 
	
        ;************************************
        ; uvmet - rotated de-staggered wind
        ;************************************
        uvmet = wrf_user_getvar(file_handle, "uvmet", time_in)
        u = uvmet(0,:,:,:,:)
	    v = uvmet(1,:,:,:,:)
        
		;************************************
        ; Interpolate vertically
        ;************************************
		u_agl   = wrf_user_intrp3d(u, hgt_agl, "h", hgts,0, False) 
        v_agl   = wrf_user_intrp3d(v, hgt_agl, "h", hgts,0, False) 
		
		
		; rename height dimesion and assign coordinate
		u_agl!1      = "height"
		u_agl&height = hgts
		v_agl!1      = "height"
		v_agl&height = hgts
		
		;************************************
        ; Interpolate horizontally
        ;************************************
        u_agl_locs = wrf_user_hinterp(nc_file, u_agl, lat, lon, xlat, xlong, opts@interp_option)
        v_agl_locs = wrf_user_hinterp(nc_file, v_agl, lat, lon, xlat, xlong, opts@interp_option)
		
		u_agl_locs!1         = "time"
		u_agl_locs&time      = ud_times
		u_agl_locs@init_time = init_time
		u_agl_locs@nest_id   = nest_id
		u_agl_locs@var_name  = "U"
		; May as well do wind speed and direction here, cheap.
		
		r2d     = 45.0/atan(1.0)                                       ;wd_e
		
	    ws_agl_locs  = sqrt(u_agl_locs*u_agl_locs + v_agl_locs*v_agl_locs)
	    ws_agl_locs@varname     = "SPEED"
		ws_agl_locs@description = "Wind speed"
		ws_agl_locs@units       = "m/s"

		wd_agl_locs  = atan2(u_agl_locs, v_agl_locs) * r2d + 180.
	    wd_agl_locs@varname     = "DIRECTION"
		wd_agl_locs@description = "Wind direction"
		wd_agl_locs@units       = "degrees from North"
		
		delete(u_agl)
		delete(v_agl)
		delete(u)
		delete(v)
		
	end if

	
	; Temperature variables. If any of these are present,compute the whole lot
	
	if (any((/vars@t, vars@tv, vars@theta, vars@thetav, vars@rib/))) then
        
		;temperature in kelvin
		tk          = wrf_user_getvar(file_handle, "tk", time)
		tk_agl      = wrf_user_intrp3d(tk, hgt_agl, "h", hgts,0, False) 
        tk_agl_locs = wrf_user_hinterp(nc_file, tk_agl, lat, lon, xlat, xlong, opts@interp_option)
		tk_agl_locs@varname = "T"
		delete(tk)
		delete(tk_agl)
		
		; water vapour mixing ratio
        qv          = wrf_user_getvar(file_handle, "QVAPOR", time)
		qv_agl      = wrf_user_intrp3d(qv, hgt_agl, "h", hgts,0, False) 
        qv_agl_locs = wrf_user_hinterp(nc_file, qv_agl, lat, lon, xlat, xlong, opts@interp_option)
		qv_agl_locs@varname     = "QV"
		delete(qv)
		delete(qv_agl)
		
		;virtual temperature
		tv_agl_locs = tk_agl_locs*(1+(0.61*qv_agl_locs))
		tv_agl_locs@varname = "TV"
		
		
		; potential temperature
	    theta          = wrf_user_getvar(file_handle, "theta", time)
		theta_agl      = wrf_user_intrp3d(theta, hgt_agl, "h", hgts,0, False) 
        theta_agl_locs = wrf_user_hinterp(nc_file, theta_agl, lat, lon, xlat, xlong, opts@interp_option)
		theta_agl_locs@varname     = "THETA"
		theta_agl_locs@description = "Potetial temperature"
        delete(theta)
		delete(theta_agl)
		
		; virtual potential temperature
	    theta_v_agl_locs = theta_agl_locs*(1+(0.61*qv_agl_locs))
		theta_agl_locs@varname     = "THETAV"
		theta_agl_locs@description = "Virtual potetial temperature"
        	
	
	end if
	
	
	;*********************************************
	; Bulk richardson number
	;
	; Jesper's method was compute Rib between two set
	; upper and lower indices
	; I think maybe I will compute it 
	; between each level and the lowest?
	; Jespers code:
	;	delta_teta_v =teta_v_profile(i,h_idx_upper,:,:)-teta_v_profile(i,h_idx_lower,:,:)
	;	delta_u      = uu_profile(i,h_idx_upper,:,:)-uu_profile(i,h_idx_lower,:,:)
	;	delta_v	     = vv_profile(i,h_idx_upper,:,:)-vv_profile(i,h_idx_lower,:,:)
	;	wspd_R_b         = sqrt(uu_profile(i,h_idx_R_b_type_2_h,:,:)^2+vv_profile(i,h_idx_R_b_type_2_h,:,:)^2) 
	;	if R_b_type.eq.1 then
	;		R_b_nr(i,:,:)=((g/dim_avg_n(t_v_profile(i,h_idx_lower:h_idx_upper,:,:),0))*delta_teta_v*delta_z)/  \
    ;                   	        ((delta_u^2)+(delta_v^2))
	;	else if R_b_type.eq.2 then
	;		R_b_nr(i,:,:)=((g/t_v_profile(i,h_idx_R_b_type_2_h,:,:))*delta_teta_v*delta_z)/  \
	;		wspd_R_b^2
	;	end if
	;	end if

	
	;**********************************************
	if isatt(vars, "rib") then
	
        ; create empt array		
		rib_agl_locs = new((/nlocs, ntimes, nhgts/), "float")
		
		; set level 0 of Rib to zero (Rib between lowest model level and itself)
		rib_agl_locs(:,:,0) = 0
	    
		; compute bulk richardson as difference between level k and lowest level
		do k=1,nhgts-1,1
    		dtheta_v = theta_v_agl_locs(:,:,k) - theta_v_agl_locs(:,:,0)
			dspeed   = ws_agl_locs(:,:,k) - ws_agl_locs(:,:,0)
            
			; AMS method. Take virtual temperature from top layer
			if (opts@rib_opt .eq. 1)
			    beta     = g/tv_agl_locs(:,:,k)
			
			; Zilankavitch. Average virtual temperature over profile.
			else
			    beta = g/dim_avg_n(theta_v_agl_locs(:,:,0:k), 2)
			end if
			
			rib_agl_locs(:,:,k)   = beta * dtheta_v * hgt_agl_locs(:,:,k) / dspeed^2

			delete(dtheta_v)
			delete(dspeed)
			delete(beta)

		end do
		
	end if
	
	if isatt(vars, "pblh") then
		pblh          = wrf_user_getvar(file_handle, "PBLH", time)
		printVarSummary(pblh)
        pblh_sfc_locs = wrf_user_hinterp(nc_file, pblh, lat, lon, xlat, xlong, opts@interp_option)
		ListPush(out_vars, pblh_sfc_locs)
		delete(pblh)
	end if

	if isatt(vars, "t2") then
		t2          = wrf_user_getvar(file_handle, "T2", time)
        t2_sfc_locs = wrf_user_hinterp(nc_file, t2, lat, lon, xlat, xlong, opts@interp_option)
		ListPush(out_vars, t2_sfc_locs)
        delete(t2)
	end if

	
	if isatt(vars, "ust") then
		ust          = wrf_user_getvar(file_handle, "UST", time)
        ust_sfc_locs = wrf_user_hinterp(nc_file, ust, lat, lon, xlat, xlong, opts@interp_option)
        ListPush(out_vars, ust_sfc_locs)
		delete(ust)
	end if

	if isatt(vars, "hfx") then
		hfx          = wrf_user_getvar(file_handle, "HFX", time)
        hfx_sfc_locs = wrf_user_hinterp(nc_file, hfx, lat, lon, xlat, xlong, opts@interp_option)
        ListPush(out_vars, hfx_sfc_locs)
		delete(hfx)
	end if

	if isatt(vars, "psfc") then
		psfc          = wrf_user_getvar(file_handle, "PSFC", time)
        psfc_sfc_locs = wrf_user_hinterp(nc_file, psfc, lat, lon, xlat, xlong, opts@interp_option)
        ListPush(out_vars, psfc_sfc_locs)        
		delete(psfc)
	end if

	if isatt(vars, "sst") then
		sst          = wrf_user_getvar(file_handle, "SST", time)
        sst_sfc_locs = wrf_user_hinterp(nc_file, sst, lat, lon, xlat, xlong, opts@interp_option)
        ListPush(out_vars, sst_sfc_locs)        
		delete(sst)
	end if
	
	
    ;******************************************************
	; Push 3D output variables to list
    ;******************************************************
	
	if isatt(vars, "u") then ListPush(out_vars, u_agl_locs)
    end if
    if isatt(vars, "v") then ListPush(out_vars, v_agl_locs)
    end if
	if isatt(vars, "direction") then ListPush(out_vars, wd_agl_locs)
    end if
    if isatt(vars, "speed") then ListPush(out_vars, ws_agl_locs)
    end if
	if isatt(vars, "tk") then ListPush(out_vars, tk_agl_locs)
    end if
	if isatt(vars, "theta") then ListPush(out_vars, theta_agl_locs)
    end if
	if isatt(vars, "rib") then ListPush(out_vars, rib_agl_locs)
	end if
	
 	return(out_vars)
	
end
;**************************************************************


;**************************************************************
; Writes an ascii representation of a time series for a 
; two-dimensional variable where first dimension is time, 
; Writes to record-based tseries format: 
; domain, model_run, model, nest_id, init_time, valid_time, variable, location_id, latitude, longitude, height, value
; 
; Propose new format (use headers!):
; domain, model_run, model, nest_id, location_id, latitude, longitude, variable, init_time, valid_time, height, value
;
; If we want this in JSON, for web charts, use a parser in Python
; making NCL write JSON is ugly.
;
; Either we can explicitly define the parameters domain, model_run etc, OR we could just 
; pass in a string array of 'metadata' to get get written on each row, OR
; we could add the metadata as attributes to the variable, speed.domain.
;
; For now, pass in metdata, data, location_ids, lats, lons. 
; Bit messy but WTF.
;
;***************************************************************

undef("write_series")
procedure write_series(series[*]:numeric,fname:string)

begin
    dims    = dimsizes(series)
    ntimes  = dims(0) 
    time    = series&time
    delete(dims)
    header = (/"domain","model_run","model","nest_id","location_id","latitude","longitude","variable","init_time","valid_time","height","value"/)
    prefix  = series@domain + "," + series@model_run + "," + series@model + "," + series@nest_id + "," + series@location +  "," + series@lat + "," + series@lon + "," +series@var_name
    ;print(prefix)
    
    
    timestrs = ut_string(time, "%Y-%N-%D %H:%M:%S") ; convert times to strings
    output   = new(ntimes+1, "string")
    output(0) = str_join(header, ",")
    do i=0,ntimes-1
        output(i+1)  =  prefix + "," + timestrs(0) + "," \
                                                 + timestrs(i) + ","\
                                                 + sprintf("%0.1f", series@height) + ","\
                                                 + sprintf("%0.2f", series(i))
                                                 
    end do
    asciiwrite(fname, output)

end

;******************************************************
; File naming convention
;
; To be consistent with existing code, files should be 
; named like: SLG_VGRD_d01_100_2012-11-17_12.txt
; where: SLG  = location_id
;          VGRD = 'standard' variable name
;          d01  = nest_id
;          100  = height above surface, integer 3-digits
; 2012-11-17_12 = fcst initial time  
;******************************************************

undef("write_vars")
procedure write_vars(vars, outdir[*]:string)

begin
    us = inttochar(95) ; underscore    

	dims    = dimsizes(vars)
    ddims   = dimsizes(dims)
	ndims   = ddims(0)
	
	; 3D variable
	if (ndims .eq. 3)
    	time      = vars&time
	    hgts      = vars&height
	    locations = vars&location
		loc_names = vars@loc_names
		lat       = vars@lat
		lon       = vars@lon
		
	    nlocs   = dims(0)
	    ntimes  = dims(1)
        nhgts   = dims(2)
        
		do n=0,nlocs<1,1
		    do k=0, nhgts-1,1
			    series = vars(n,:,k)
				ihgt = floattoint(hgts(k))
                shgt = sprinti("%0.3i", ihgt)
				
				series@loc_id = locations(n)
				series@height = shgt
                series@lat = lat(n)
                series@lon = lon(n)
                series@loc_name = loc_name(n)				
			
				fname   = outdir + "/" +\
                     locations(n) + us +\
                     series@var_name + us + "d" +\
                     series@nest_id + us +\
                     shgt+ us +\
                     series@init_time +".txt"
					write_series(series, fname)
					delete(series)
					delete(fname)
					delete(ihgt)
					delete(shgt)
			end do
			
		end do

	end if 
    
	if (ndims .eq. 2)
	    nlocs = dims(0)
		ntimes = dims(1)
    end if

end
