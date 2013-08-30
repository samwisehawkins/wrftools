load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/ut_string.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl" 
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
;load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
load "$WRFTOOLS/ncl/WRFUserARW.ncl"
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
  
  
  out    = [/loc_id, name, lat, lon/]

  
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
		; if var(time, level, y, x)
        if (ndims .eq. 4)
		    var_out = new((/nlocs,ntimes,nhgts/),"float")
            
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
  
    if (opts@latlon .eq. 0)  
        xlat  = nc_file->XLAT(0,:,:) ; latitudes don't change over time
        xlong = nc_file->XLONG(0,:,:)
    end if
 
    if (opts@latlon .eq. 1)  
        xlat  = nc_file->XLAT(:,:) ; latitudes don't change over time
        xlong = nc_file->XLONG(:,:)
    end if

    dims = dimsizes(xlat)
    south_north = dims(0)
    west_east   = dims(1)
    delete(dims)
    
    times     = nc_file->Times
    ud_times  = wrf_times_c(times, 0)
    init_time = chartostring(times(0,0:12))

	; time of -1 gets all timesteps, otherwise we are feching one timestep
    dims = dimsizes(times)
    if (time .eq. -1) then 
        ntimes=dims(0)
    else ntimes=1
    end if
    delete(dims)
	
    
   
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
    if opts@reduced
        hgt_ter       = file_handle->HGT(:,:)                       ; assume terrain doesn't change with time
        hgt_amsl      = wrf_user_getvar(file_handle, "z", time)     ; height above sea level of model levels
                                                                    ; this will be 4D, since height varies (slightly) hgt_amsl(time, level, y,x)
    else
        hgt_ter       = wrf_user_getvar(file_handle, "ter", 0)      ; assume terrain doesn't change with time
        hgt_amsl      = wrf_user_getvar(file_handle, "z", time)     ; height above sea level of model levels
                                                                    ; this will be 4D, since height varies (slightly) hgt_amsl(time, level, y,x)
     end if

    
    
                                                                
	hgt_new = conform(hgt_amsl, hgt_ter, (/2,3/))               ; ensure they terrain height is right dimensionality
    hgt_agl = hgt_amsl - hgt_new                                ; get the height of model levels above ground level
	
	hgt_agl_locs = wrf_user_hinterp(nc_file, hgt_agl, lat, lon, xlat, xlong, opts@interp_option)
	delete(hgt_new)
    
 
    if( any( (/vars@u, vars@v, vars@rib, vars@speed, vars@direction/) ) ) then 
	
        ;************************************
        ; uvmet - rotated unstaggered wind
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
		
		u_agl_locs!1         = "Time"
		u_agl_locs&Time      = ud_times
		u_agl_locs@init_time = init_time
		u_agl_locs@nest_id   = nest_id
		u_agl_locs@varname  = "U"

		v_agl_locs!1         = "Time"
		v_agl_locs&Time      = ud_times
		v_agl_locs@init_time = init_time
		v_agl_locs@nest_id   = nest_id
		v_agl_locs@varname  = "V"


		; Wind speed and direction
		
		r2d     = 45.0/atan(1.0)
     
	    ws_agl_locs  = sqrt(u_agl_locs*u_agl_locs + v_agl_locs*v_agl_locs)
        ws_agl_locs!0="location"
        ws_agl_locs!1="Time"
        ws_agl_locs!2="height"
        ws_agl_locs&height = hgts
   
        ws_agl_locs@varname     = "SPEED"
		ws_agl_locs@description = "Wind speed"
		ws_agl_locs@units       = "m/s"

		wd_agl_locs  = atan2(u_agl_locs, v_agl_locs) * r2d + 180.
	    wd_agl_locs!0="location"
        wd_agl_locs!1="Time"
        wd_agl_locs!2="height"
        wd_agl_locs&height = hgts

	    wd_agl_locs@varname     = "DIRECTION"
		wd_agl_locs@description = "Wind direction"
		wd_agl_locs@units       = "degrees from North"
		
		delete(u_agl)
		delete(v_agl)
		delete(u)
		delete(v)
		
	end if

	
	; 3D Temperature variables. If any of these are present,compute the whole lot
	
	if (any((/vars@t, vars@tv, vars@theta, vars@thetav, vars@rib/))) then
        
		;temperature in kelvin
		tk          = wrf_user_getvar(file_handle, "tk", time)
		tk_agl      = wrf_user_intrp3d(tk, hgt_agl, "h", hgts,0, False)
        
        tk_agl!1      = "height"
		tk_agl&height = hgts
        
        tk_agl_locs = wrf_user_hinterp(nc_file, tk_agl, lat, lon, xlat, xlong, opts@interp_option)
		tk_agl_locs@varname = "T"
		printVarSummary(tk_agl_locs)
        tc_agl_locs = tk_agl_locs -273.15
        tc_agl_locs@units = "C"
        tc_agl_locs!0 = "location"
        tc_agl_locs!1 = "Time"
        tc_agl_locs!2 = "height"
        copy_VarMeta(tk_agl_locs, tc_agl_locs)
        delete(tk)
		delete(tk_agl)
		
		; water vapour mixing ratio
        qv          = wrf_user_getvar(file_handle, "QVAPOR", time)
		qv_agl      = wrf_user_intrp3d(qv, hgt_agl, "h", hgts,0, False) 
        qv_agl_locs = wrf_user_hinterp(nc_file, qv_agl, lat, lon, xlat, xlong, opts@interp_option)
		qv_agl_locs@varname     = "QVAPOR"
		delete(qv)
		delete(qv_agl)
		printVarSummary(qv_agl_locs)
		
        ;virtual temperature
		tv_agl_locs = tk_agl_locs*(1+(0.61*qv_agl_locs))
		tv_agl_locs@varname = "TV"
		
		
		; potential temperature
	    theta          = wrf_user_getvar(file_handle, "theta", time)
		theta_agl      = wrf_user_intrp3d(theta, hgt_agl, "h", hgts,0, False) 
        theta_agl_locs = wrf_user_hinterp(nc_file, theta_agl, lat, lon, xlat, xlong, opts@interp_option)
        
        theta_agl_locs!2          = "height"        	
        theta_agl_locs&height      = hgts
		theta_agl_locs@varname     = "THETA"
		theta_agl_locs@description = "Potetial temperature"
        delete(theta)
		delete(theta_agl)
		
		; virtual potential temperature
	    thetav_agl_locs = theta_agl_locs*(1+(0.61*qv_agl_locs))
		printVarSummary(thetav_agl_locs)
        
        thetav_agl_locs@varname     = "THETAV"
		thetav_agl_locs@description = "Virtual potetial temperature"
        thetav_agl_locs!0          = "location"
        thetav_agl_locs!1          = "Time"
        thetav_agl_locs!2          = "height"        	
        thetav_agl_locs&height      = hgts
    
	end if
	
	
	;*********************************************
	; Bulk richardson number
	;
	; Jesper's method was compute Rib between two set
	; upper and lower indices
	; I think maybe I will compute it 
	; between each level and the lowest?
    ; Probably we should set options opt@rib_lower=10, opt@rib_upper=30
    ;
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
	

	if vars@rib
	
        ; create empt array		
		rib_agl_locs = new((/nlocs, ntimes, nhgts/), "float")
		
		; set level 0 of Rib to zero (Rib between lowest model level and itself)
		rib_agl_locs(:,:,0) = 0
	    
		; compute bulk richardson as difference between level k and lowest level
		do k=1,nhgts-1,1
    		dtheta_v = thetav_agl_locs(:,:,k) - thetav_agl_locs(:,:,0)
			dspeed   = ws_agl_locs(:,:,k) - ws_agl_locs(:,:,0)
            
			; AMS method. Take virtual temperature from top layer
			if (opts@rib_opt .eq. 1)
			    beta     = g/tv_agl_locs(:,:,k)
			
			; Zilankavitch. Average virtual temperature over profile.
			else
			    beta = g/dim_avg_n(thetav_agl_locs(:,:,0:k), 2)
			end if
			
			rib_agl_locs(:,:,k)   = beta * dtheta_v * hgt_agl_locs(:,:,k) / dspeed^2

			delete(dtheta_v)
			delete(dspeed)
			delete(beta)

		end do
		rib_agl_locs@varname = "RIB"
        rib_agl_locs!0       = "location"
        rib_agl_locs!1       = "Time"
        rib_agl_locs!2       = "height"
        rib_agl_locs&height  = hgts
	end if
	
    
    if vars@rain
        rainc  = wrf_user_getvar(file_handle, "RAINC", time) 
        rainnc = wrf_user_getvar(file_handle, "RAINNC", time) 
        rain   = rainc+rainnc
        rain_sfc_locs = wrf_user_hinterp(nc_file, rain, lat, lon, xlat, xlong, opts@interp_option)
    
    ; Convert to rain per hour
        do n=1,ntimes-2
            k = ntimes-n
            rain_sfc_locs(:, k) = rain_sfc_locs(:,k)-rain_sfc_locs(:,k-1)
        end do
        
        rain_sfc_locs@varname = "RAIN"
        rain_sfc_locs@height = 0
    
    end if
    
	if vars@pblh
		pblh          = wrf_user_getvar(file_handle, "PBLH", time)
        pblh_sfc_locs = wrf_user_hinterp(nc_file, pblh, lat, lon, xlat, xlong, opts@interp_option)
        pblh_sfc_locs@varname = "PBLH"
        pblh_sfc_locs@height = 0
		ListPush(out_vars, pblh_sfc_locs)
		delete(pblh)
	end if

	if vars@t2 then
		t2          = wrf_user_getvar(file_handle, "T2", time)
        t2_sfc_locs = wrf_user_hinterp(nc_file, t2, lat, lon, xlat, xlong, opts@interp_option)
		t2_sfc_locs@varname = "T2"
        t2_sfc_locs@height  = 2
        ListPush(out_vars, t2_sfc_locs)
        delete(t2)
	end if

	
	if vars@ust then
		ust          = wrf_user_getvar(file_handle, "UST", time)
        ust_sfc_locs = wrf_user_hinterp(nc_file, ust, lat, lon, xlat, xlong, opts@interp_option)
        ust_sfc_locs@varname = "UST"
        ust_sfc_locs@height = 0
        ListPush(out_vars, ust_sfc_locs)
		delete(ust)
	end if

	if vars@hfx then
		hfx          = wrf_user_getvar(file_handle, "HFX", time)
        hfx_sfc_locs = wrf_user_hinterp(nc_file, hfx, lat, lon, xlat, xlong, opts@interp_option)
        hfx_sfc_locs@varname = "HFX"
        hfx_sfc_locs@height = 0
        ListPush(out_vars, hfx_sfc_locs)
		delete(hfx)
	end if

	if vars@psfc then
		psfc          = wrf_user_getvar(file_handle, "PSFC", time)
        psfc_sfc_locs = wrf_user_hinterp(nc_file, psfc, lat, lon, xlat, xlong, opts@interp_option)
        psfc_sfc_locs@varname = "PSFC"
        psfc_sfc_locs@height = 0
        ListPush(out_vars, psfc_sfc_locs)        
		delete(psfc)
	end if

	if vars@sst then
		sst          = wrf_user_getvar(file_handle, "SST", time)
        sst_sfc_locs = wrf_user_hinterp(nc_file, sst, lat, lon, xlat, xlong, opts@interp_option)
        sst_sfc_locs@varname = "SST"
        sst_sfc_locs@height = 0
        ListPush(out_vars, sst_sfc_locs)        
		delete(sst)
	end if

    if vars@tsk then
		tsk          = wrf_user_getvar(file_handle, "TSK", time)
        tsk_sfc_locs = wrf_user_hinterp(nc_file, tsk, lat, lon, xlat, xlong, opts@interp_option)
        tsk_sfc_locs@varname = "TSK"
        tsk_sfc_locs@height = 0
        ListPush(out_vars, tsk_sfc_locs)        
		delete(tsk)
	end if
    
    if vars@ust then
		ust          = wrf_user_getvar(file_handle, "UST", time)
        ust_sfc_locs = wrf_user_hinterp(nc_file, ust, lat, lon, xlat, xlong, opts@interp_option)
        ust_sfc_locs@varname = "TSK"
        ust_sfc_locs@height = 0
        ListPush(out_vars, ust_sfc_locs)        
		delete(ust)
	end if

    if vars@hfx then
		hfx          = wrf_user_getvar(file_handle, "HFX", time)
        hfx_sfc_locs = wrf_user_hinterp(nc_file, hfx, lat, lon, xlat, xlong, opts@interp_option)
        hfx_sfc_locs@varname = "HFX"
        hfx_sfc_locs@height = 0
        ListPush(out_vars, hfx_sfc_locs)        
		delete(hfx)
	end if

    
    
    
    
    
    
	if vars@swdown then
		swdown  = wrf_user_getvar(file_handle, "SWDOWN", time)
        swdown_sfc_locs = wrf_user_hinterp(nc_file, swdown, lat, lon, xlat, xlong, opts@interp_option)
		swdown_sfc_locs@varname = "SWDOWN"
        swdown_sfc_locs@height  = 0
        ListPush(out_vars, swdown_sfc_locs)
        delete(swdown)
	end if

	if any((/vars@cldfraavg, vars@cldframax/)) then
		cldfra             = wrf_user_getvar(file_handle, "CLDFRA", time)
        cldfra_sfc_locs    = wrf_user_hinterp(nc_file, cldfra, lat, lon, xlat, xlong, opts@interp_option)
		cldfraavg_sfc_locs = dim_avg_n_Wrap(cldfra_sfc_locs, 1)
        cldframax_sfc_locs = dim_max_n(cldfra_sfc_locs, 1)
        cldfraavg_sfc_locs@height = 0
        cldframax_sfc_locs@height = 0
        if vars@cldfraavg
            ListPush(out_vars, cldfraavg_sfc_locs)
        end if
        if vars@cldframax
            ListPush(out_vars, cldframax_sfc_locs)
        end if
        delete(cldfra)
    end if


	
    ;******************************************************
	; Push 3D output variables to list
    ;******************************************************
	
	if vars@u then ListPush(out_vars, u_agl_locs)
    end if
    if vars@v then ListPush(out_vars, v_agl_locs)
    end if
	if vars@direction then ListPush(out_vars, wd_agl_locs)
    end if
    if vars@speed then ListPush(out_vars, ws_agl_locs)
    end if
	if vars@t then ListPush(out_vars, tc_agl_locs)
    end if
	if vars@theta then ListPush(out_vars, theta_agl_locs)
    end if
	if vars@thetav then ListPush(out_vars, thetav_agl_locs)
    end if
    if vars@rib then ListPush(out_vars, rib_agl_locs)
	end if
	

    ;******************************************************
	; Fix time coordinate
    ;******************************************************

	nvars = ListCount(out_vars)
	do i=0,nvars-1
        printVarSummary(out_vars[i])
        out_vars[i]&Time   = ud_times
    end do
    
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
    delete(dims)
    if (iscoord(series, "time"))
        time =     series&time
    else
        time =     series&Time
    end if
    
    header = (/"domain","model_run","model","nest_id","location_id","latitude","longitude","variable","init_time","valid_time","height","value"/)
    prefix  = series@domain + "," + series@model_run + "," + series@model + "," + series@nest_id + "," + series@location +  "," + series@lat + "," + series@lon + "," +series@varname
    
    
    timestrs = ut_string(time, "%Y-%N-%D %H:%M:%S") ; convert times to strings
    output   = new(ntimes+1, "string")
    output(0) = str_join(header, ",")

    if isnumeric(series@height)
        do i=0,ntimes-1
            output(i+1)  =  prefix + "," + timestrs(0) + "," \
                                                 + timestrs(i) + ","\
                                                 + sprintf("%0.1f", series@height) + ","\
                                                 + sprintf("%0.2f", series(i))
                                                 
        end do
    end if
    if isstring(series@height)
        do i=0,ntimes-1
            output(i+1)  =  prefix + "," + timestrs(0) + "," \
                                                 + timestrs(i) + ","\
                                                 + series@height + ","\
                                                 + sprintf("%0.2f", series(i))
                                                 
        end do
    end if






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
                     series@varname + us + "d" +\
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
