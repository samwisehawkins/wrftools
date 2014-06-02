load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/ut_string.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl" 
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
;load "$WRFTOOLS/ncl/WRFUserARW.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRF_contributed.ncl"

;******************************************************
; Blank pad a string to fixed length
;******************************************************
undef("blank_pad")
function blank_pad (strs, length) ; extend a string to fixed length 
local n, strs, str
begin 
   dims = dimsizes(strs)
   nstrs = dims(0)
   do n=0, nstrs-1
       str = strs(n)
       nextra = length - strlen (str) -1
       if (nextra .ge. 1) then 
          bbb = new (nextra, string) 
          bbb(:) = " " 
          strs(n) = (str + str_concat (bbb)) 
       else 
          strs(n) = str
       end if 
    end do
   return strs
   
end 



;******************************************************
; Read locations from file with named columns
;******************************************************
undef("read_locations")
function read_locations(loc_file)

begin
  loc_str_len = 6
  cmd       = "sed  '/^[[:space:]]*#/d' " + loc_file          ; skip any commented lines
  lines     = systemfunc(cmd)                                 ; take input from sed
  header    = str_split(lines(0), ",")                        ; first line is header 
  data      = lines(1:)                                       ; rest is data

  loc_ind   = str_match_ind_ic(header, "location_id")         ; find which columns to get
  lat_ind   = str_match_ind_ic(header, "latitude")            
  lon_ind   = str_match_ind_ic(header, "longitude")
  name_ind  = str_match_ind_ic(header, "name")

  loc_id    = str_get_field(data, loc_ind+1, ",")                ; str_get_field numbering starts at 1
  loc_id_l  = blank_pad(loc_id, loc_str_len)                     ; pad with blanks in case id is shorter than loc_str_len
  lat       = stringtofloat(str_get_field(data, lat_ind+1, ",")) ; so add 1 to indices
  lon       = stringtofloat(str_get_field(data, lon_ind+1, ","))
  name      = str_get_field(data, name_ind+1, ",")
  
  
  out    = [/loc_id_l, name, lat, lon/]
  return(out)

end






;*****************************************************************************
; Horizontally interpolate to a set of locations
; interp_option: 0 nearest cell (as found by ll_to_ij)
;                1 inverse distance weighting as implemented by rcm2points(opt=1)
;                2 bilinear interpolation as implemented by rcm2points(opt=2)
;*****************************************************************************
undef("wrf_user_hinterp")
function wrf_user_hinterp(nc_file, var, lat, lon, xlat, xlong, interp_option)

begin
    dims   = dimsizes(var)
    ddims  = dimsizes(dims)
    ndims  = ddims(0)
    ;print(ndims)  
    
    delete(dims)
    delete(ddims)
    
    dims = dimsizes(lat)
    nloc = dims(0)
    delete(dims)

    ; 4D variable(time,height,y, x)
    if (ndims .eq. 4)
        dims        = dimsizes(var)
        ntime       = dims(0)
        nheight     = dims(1)
        south_north = dims(2)
        west_east   = dims(3)
        delete(dims)
    end if
    
    ; 3D variable(time,y, x)
    if (ndims .eq. 3)
        dims        = dimsizes(var)
        ntime       = dims(0)
        south_north = dims(1)
        west_east   = dims(2)
        delete(dims)
    end if
    
    ;print(south_north)
    ;print(west_east)
    
    ;******************************************************
    ; Enclosing cell interpolation
    ;******************************************************
    if (interp_option.eq.0) ; enclosing cell, no interpolation
        
        ;******************************************************
        ; Get ij locations
        ij   = wrf_user_ll_to_ij(nc_file,lon, lat, True)
        loc  = ij-1          ; To convert to NCL subscripts
        ;******************************************************
        
        ; if var(time, level, y, x)
        if (ndims .eq. 4)

            ; need to create variable with a shape which can be assigned to easily
            ; then we can reshape later if needed
            ; rcm2points replaces the last two dimensions, y and x with location
            ; perhaps we should mimic that?
            var_out = new((/ntime,nheight,nloc/),"float")

            do n=0,nloc-1
                ;print(loc(:,n))
                ; if location is outside domain
                if ( (loc(1,n) .ge. south_north) .or. (loc(0,n) .ge. west_east))
                    print("Warning, location is outside domain, values will be missing")
                    var_out(n,:,:) = default_fillvalue("float")
                else
                    ; var(time, level, y, x)
                    y = loc(1,n)
                    x = loc(0,n)
                    ;print(y)
                    ;print(x)
                    var_out(:,:,n) = var(:,:,y,x)
                end if
            end do
        end if
        
        ; if var(time, y, x)
        if (ndims .eq. 3)
            var_out = new((/ntime, nloc/),"float")
            do n=0,nloc-1
                if ( (loc(1,n) .ge. south_north) .or. (loc(0,n) .ge. west_east))
                    print("Warning, location is outside domain, values will be missing")
                    var_out(n,:) = default_fillvalue("float")
                else
                    var_out(:,n) = var(:,loc(1,n),loc(0,n))
                end if
            end do
        end if

    ;******************************************************
    ; rcm2points interpolation
    ;******************************************************
    else
        ; rcm2points will replace the last 2 dimensions with 1 dimension, 
        ; which is the locations
        printVarSummary(xlat)
        printVarSummary(xlong)
        printVarSummary(var)
        printVarSummary(lat)
        printVarSummary(lon)
        printVarSummary(interp_option)
        var_out = rcm2points(xlat, xlong,  var, lat, lon, interp_option)
    end if        
    
    ;******************************************************
    ; remove any staggering information
    ; variable is no longer staggered if we have iterpolated to points
    ;******************************************************

    if (isatt(var_out, (/"stagger"/)))
        delete_VarAtts(var_out, "stagger")
    end if
    if (isatt(var_out, (/"coordinates"/)))
        delete_VarAtts(var_out,  "coordinates")
    end if
    
    ;******************************************************
    ; Give variable correct units
    ;******************************************************
    var_out@units = var@units
    var_out@description = var@description

    ;******************************************************
    ; Give dimensions correct names and reorder
    ;******************************************************
    if (ndims .eq. 4)     ; var_in(time,height,y, x) --> var_out(time,height,loc)
        var_out!0="time"
        var_out!1="height"
        var_out!2="location"
        ;return var_out(location|:,height|:, time|:)
        return var_out(time|:,location|:,height|:)
    end if
        
    if (ndims .eq. 3)     ; var_in(time,y, x) --> var_out(time,loc)
        var_out!0="time"
        var_out!1="location"
        ;return var_out(location|:, time|:)
        return var_out(time|:, location|:)
    end if

    
end



;*******************************************************************************
;
; wrf_user_interp_vars_tofile
; Horizontally and vertically interpolates variables and new diagnostics 
; to a set of locations. Vertical interpolation of the variables is done first,
; using wrf_user
;
; Arguments:
; file_handle: wrfout files to extract from
; height: array of heights to extract to
; lat: array of latitudes to interpolate to
; lon: array of longitudes to interpoate to
; loc_ids: array of location_id strings to be used as coordinate variables
; time_in: which timestep to get, -1 gets all timesteps
; file_out: name of (netcdf) file to write to
; vars: boolean object with attributes specifying which variables to fetch. See below.
; opt: various options, currently
;      opt@time_units: 0 returns units of "hours since" initial time on the current file (type "double")
;                      1 returns units of "hours since 1901-01-01 00:00:00" (type "double")
;                      2 returns units of "yyyymmddhhmnss" (type "double")
;                      3 returns units of "yyyymmddhh" (type "integer")
;      opt@h_interp: horizontal interpolation option
;      opt@rb_type: bulk richardson computation type
;      opt@rb_lower: lower height for Bulk Richardson
;      opt@rb_upper: upper height for Bulk Richardson
;
; The output of 3D vars will be var(location, height, time)
; 2D vars will be var(location, height, time)
;
;*******************************************************************************

undef("wrf_user_interp_vars_tofile")
function wrf_user_interp_vars_tofile(file_handle, hgt_out[*]:numeric, location[*]:string, lat[*]:numeric, lon[*]:numeric,time_in:integer, file_out, vars, opts)
local variable, time, var, u, v, u_in, v_in, pii, radians_per_degree, \
dims, nd, xlat, xlong, rank, \
R, g, cp, lv, t

begin

    ;******************************************************
    ; Print some information
    ;******************************************************
    print("Interpolating WRF variables to locations and heights")
    ;print(vars)
    ;print(opts)


    ;******************************************************
    ; Constants / hard coded options
    ;******************************************************
    radians_per_degree = 0.0174532925
    R  = 287.058            ; gas constant for air
    g  = 9.81               ; gravitational acceleration
    cp = 1003.5             ; specific heat capacity of air
    lv = 2400000            ; latent heat of evaporation 
    c_to_k = 273.15         ; degrees C to Kelvin 
 
    
    ;******************************************************
    ; File handle. Allows multiple files to be used
    ; nc_file gives refers to single file
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
    t          = time_in(0)
    variables  = getvaratts(vars)
    ;******************************************************

    
    ;******************************************************
    ; Create dimensions
    ; Latitudes, longitudes, times, locations
    ; Dimension sizes
    ;******************************************************
    
    loc_str_length = 6 ; hard coded length of loc IDs
    dims      = dimsizes(hgt_out)
    nheight   = dims(0)
    delete(dims)

    dims  = dimsizes(location)
    nloc  = dims(0)
    delete(dims)
  
    ;*******************************************************
    ; Work out if lat and lon are time-invariant
    ;*******************************************************
    dims = getfilevardims(nc_file,"XLAT")        
    ndims = dimsizes(dims)
    
    if (ndims .eq. 3) ; lat and lon are 3D, lat(time, y, x)
        xlat  = nc_file->XLAT(0,:,:) 
        xlong = nc_file->XLONG(0,:,:)
    end if 
  
    if (ndims .eq. 2); lat and lon are 2D, lat(y,x)
        xlat  = nc_file->XLAT(:,:) ; latitudes don't change over time
        xlong = nc_file->XLONG(:,:)
    end if
    delete(dims)
    delete(ndims)

    dims = dimsizes(xlat)
    south_north = dims(0)
    west_east   = dims(1)
    delete(dims)
    
    ;*******************************************************
    ; Convert time units
    if(ISFILE) then
        time_c     = file_handle->Times
    else
        time_c     = file_handle[:]->Times
    end if
    
    
    
    time_s    = chartostring(time_c)                     ; string
    print(time_s)
    time       = wrf_times_c(time_c, opts@time_units) 
    init_time  = ut_string(time(0), "%Y-%m-%d_%H:%M:%S")

    
    
    ; t of -1 gets all timesteps, otherwise we are feching one timestep
    dims = dimsizes(time)
    if (t    .eq. -1) then 
        ntime=dims(0)
    else ntime=1
    end if
    delete(dims)
    delete(time_c)
    ;*******************************************************    
    
    
    ;******************************************************    
    ; Now we have all the dimensions needed
    ; nheight :     number of vertical levels for 3D vars
    ; nlocation:    number of locations we are interpolating to
    ; ntime:        number of timetseps to extract 
    ; south_north:  south north extent
    ; west_east:    west east extent
    ;******************************************************    

    ;******************************************************    
    ; Create a template for 2D and 3D variables
    ;******************************************************    

    ;v2d_template = new((/nloc,ntime/),"float")
    ;v3d_template = new((/nloc,nheight,ntime/),"float")

    v2d_template = new((/ntime,nloc/),"float")
    v3d_template = new((/ntime,nloc,nheight/),"float")
    
    
    v2d_template!0    = "time"
    v2d_template!1    = "location"    
    v2d_template&time = time

    v3d_template!0    = "time"
    v3d_template!1    = "location"
    v3d_template!2    = "height"    
    v3d_template&height = hgt_out
    v3d_template&time   = time

    dims_2d = (/"time", "location"/)                
    dims_3d = (/"time", "location", "height"/)                         
    ;******************************************************    

    
    ;******************************************************    
    ; Create the output file
    ;******************************************************    
    system("/bin/rm -f " + file_out)                  ; remove if exists
    ;setfileoption("nc", "usenewhlfs", True)
    setfileoption("nc", "Format", "NetCDF4Classic")   ; set to NetCDF4
    fout  = addfile (file_out, "c")                   ; open output file
    

    ;******************************************************    
    ; explicitly declare file definition mode. Improve efficiency.
    ;******************************************************    
    setfileoption(fout,"DefineMode",True)

    ;******************************************************    
    ; create global attributes of the file
    ;******************************************************    
    atts =  getvaratts(nc_file);
    print("setting global attributes - hard-coded as copy did not work")
    
    
    
    fAtt               = True            ; assign file attributes
    fAtt@title         = "WRF time series interpolated to locations"  ; hack to change title in output
    fAtt@Conventions   = "None"   
    fAtt@creation_date = systemfunc ("date")        
    fAtt@GRID_ID       = nc_file@GRID_ID
    fAtt@DOMAIN        = nc_file@DOMAIN
    fAtt@MODEL_RUN     = nc_file@MODEL_RUN
    fAtt@DX            = nc_file@DX
    fAtt@DY             = nc_file@DY
    fAtt@BDY_CONDITIONS = nc_file@BDY_CONDITIONS
    fAtt@MODEL          = nc_file@MODEL
    
    fileattdef(fout, fAtt )           ; copies global attributes to the tseries file
    
    
    ;******************************************************    
    ; predefine the coordinate variables and their dimensionality
    ; Note: to get an UNLIMITED record dimension, we set the dimensionality
    ; to -1 (or the actual size) and set the dimension name to True.
    ;******************************************************    
    dimNames = (/"time", "location", "height", "loc_str_length"/)  
    dimSizes = (/ -1   , nloc,  nheight, loc_str_length/) 
    dimUnlim = (/ True , False, False, False/)   
    filedimdef(fout,dimNames,dimSizes,dimUnlim)
    
    
    ;******************************************************    
    ; predefine the the dimensionality of the variables to be written out
    ;******************************************************    
    ; Here we are using NCL functions to facilitate defining 
    ; each variable's dimension name(s) and type. 
    ; The following could be replaced with explicit, user defined dimension 
    ; names different from those associated with the variable in memory. 
    ; Say, PS(time,lat,lon) in the NCL script. They could be redefined for the file via: 
    ; filevardef(fout, "PS"   ,typeof(PS) ,(/"TIME","latitude","longitude"/)) 
    ;******************************************************    

    filevardef(fout, "time" ,  typeof(time),(/"time"/)) 
    filevarattdef(fout,"time" ,time)                    ; copy time attributes
        

    filevardef(fout, "height", typeof(hgt_out),(/"height"/))                           
    hgt_out@units = "metres"
    hgt_out@description="metres above the ground or water surface"

    loc_char = stringtochar(location)
    loc_char@description = "site location identified by ID" 
    filevardef(fout, "location",typeof(loc_char),(/"location", "loc_str_length"/))                           
    
    filevardef(fout, "lat" ,  typeof(lat),(/"location"/)) 
    lat@units       = "degrees north"
    lat@description = "latitude" 
    filevarattdef(fout, "lat", lat)                   
    
    filevardef(fout, "lon" ,  typeof(lon),(/"location"/)) 
    lon@units       = "degrees east"
    lon@description = "longitude" 
    filevarattdef(fout,"lon", lon) 
    
    ;******************************************************    
    ; output only the data values since the dimensionality and such have
    ; been predefined. The "(/", "/)" syntax tells NCL to only output the
    ; data values to the predefined locations on the file.
    ;******************************************************    
    ;printVarSummary(loc_char)
    ;print(loc_str_length)
    fout->time     = (/time/)     
    fout->location = (/loc_char(:,0:loc_str_length-1)/)
    fout->height   = (/hgt_out/) 
    fout->lat      = (/lat/)
    fout->lon      = (/lon/)
    ;******************************************************    
    
    
    ;******************************************************    
    ; FILE DEFINITION FINISHED
    ; NOW GET THE DATA!
    ;******************************************************    
   
    ;******************************************************
    ; Get ij locations
    ; Do we still need these?
    ij   = wrf_user_ll_to_ij(nc_file,lon, lat, True)
    loc  = ij-1          ; To convert to NCL subscripts
    ;******************************************************
  
    ;******************************************************
    ; Get basic variables we will *always* need
    ;******************************************************
 
    ;******************************************************
    ; Height of model levels above sea level
    ;******************************************************    
    hgt_amsl      = wrf_user_getvar(file_handle, "z", t)     ; height above sea level of model levels
                                                             ; this will be 4D, since height varies (slightly) hgt_amsl(time, level, y,x)
 
    ;******************************************************
    ; Terrain height
    ;******************************************************    
    dims = getfilevardims(nc_file,"HGT")        
    ndims = dimsizes(dims)

    if (ndims .eq. 3)                                        ; terrain height varies with time, i.e. to support moving nest
        if(ISFILE) then
            hgt_ter_i       = file_handle->HGT(0,:,:)        ; get terrain height at first
        else
            hgt_ter_i       = file_handle[0]->HGT(0,:,:)     ; get terrain height at first
        end if
        
        ; hgt_amsl(time, level, y, x)
        ; hgt_ter_i(y, x)
        hgt_ter         = conform(hgt_amsl, hgt_ter_i, (/2,3/))      ; add a level dimension 
    
    end if                                                           ; for easy subtraction with level heights                   
    
    if (ndims .eq. 2) ; terrain height doesn't vary with time
        hgt_ter_i     = file_handle[0]->HGT(:,:)                    ; height already invariant
        hgt_ter = conform(hgt_amsl, hgt_ter_i, (/2,3/))             ; so add time and level dimension 
    end if         
    
    ;******************************************************
    ; Height of model levels above terrain level
    ;******************************************************    
    hgt_agl = hgt_amsl - hgt_ter                                    ; get the height of model levels above ground level
    hgt_agl@units = "metres"
    
    delete(hgt_amsl)
    delete(hgt_ter)
    delete(hgt_ter_i)
    
    ;******************************************************
    ; Horizontally interolate the height of model levels to the locations
    ;******************************************************    
    ;printVarSummary(lat)
    ;printVarSummary(lon)
    ;printVarSummary(xlat)
    ;printVarSummary(xlong)
    ;printVarSummary(hgt_agl)
    hgt_agl_locs = wrf_user_hinterp(nc_file, hgt_agl, lat, lon, xlat, xlong, opts@interp_option)
    
    
 
    ;******************************************************
    ; Do we need to calculate wind speed?
    ;******************************************************
     if( any( (/vars@u, vars@v, vars@rib, vars@speed, vars@direction/) ) ) then 
    
        ;************************************
        ; uvmet - rotated unstaggered wind
        ;************************************
        uvmet = wrf_user_getvar(file_handle, "uvmet", time_in)
        ul = uvmet(0,:,:,:,:)
        vl = uvmet(1,:,:,:,:)
        
        uvmet10 = wrf_user_getvar(file_handle, "uvmet10", time_in)
        u10 = uvmet10(0,:,:,:)
        v10 = uvmet10(1,:,:,:)
        
        
        u = merge_levels_sfc(ul, u10, -1)
        v = merge_levels_sfc(vl, v10, -1)

        delete(uvmet)
        delete(uvmet10)
        delete(ul)
        delete(vl)
        

        
        ; will be time, level, south_north, west_east
        delete(dims)
        dims = dimsizes(hgt_agl)
        
        ; we have one extra height level for wind, due to 10m diagnostic
        hgt_agl_uv = new((/dims(0), dims(1)+1, dims(2), dims(3)/), float) 
        hgt_agl_uv(:, 1:dims(1), :, :) = hgt_agl(:, :, :, :)
        hgt_agl_uv(:,0,:,:) = 10.0
        
        delete(dims)
        

        u@description = "eastward component of wind velocity"
        v@description = "northward component of wind velocity"

        ;************************************
        ; Vertically interpolate wind speeds to height levels
        ;************************************
        u_agl   = wrf_user_intrp3d(u, hgt_agl_uv, "h", hgt_out,0, False) 
        v_agl   = wrf_user_intrp3d(v, hgt_agl_uv, "h", hgt_out,0, False) 

        delete(u)
        delete(v)
        
        ;************************************
        ; Interpolate wind speed horizontally
        ;************************************
        u_agl_locs = wrf_user_hinterp(nc_file, u_agl, lat, lon, xlat, xlong, opts@interp_option)
        v_agl_locs = wrf_user_hinterp(nc_file, v_agl, lat, lon, xlat, xlong, opts@interp_option)

        delete(u_agl)
        delete(v_agl)

        
        ; Put the variables into the file
        if vars@u
            filevardef(fout, "U", typeof(u_agl_locs), dims_3d)
            filevarattdef(fout,"U", u_agl_locs) 
            u_agl_locs@description = "eastward component of wind speed"
            u_agl_locs@units       = "m/s"
            fout->U     = (/u_agl_locs/)
            filevarattdef(fout,"U", u_agl_locs)
        end if
        
        if vars@v
            filevardef(fout, "V",typeof(v_agl_locs),dims_3d)
            v_agl_locs@description = "northward component of wind speed"
            v_agl_locs@units       = "m/s"
            fout->V     = (/v_agl_locs/)
            filevarattdef(fout,"V", v_agl_locs)
        end if
        
        ; Wind speed
        ws_agl_locs  = sqrt(u_agl_locs*u_agl_locs+v_agl_locs*v_agl_locs)
        
        ; rename the dimensions, sqrt strips any info
        copy_VarMeta(v3d_template, ws_agl_locs) 
        ws_agl_locs&height = hgt_out
        ws_agl_locs&time   = time
        ws_agl_locs@description = "wind speed"
        ws_agl_locs@units       = "m/s"

        if vars@speed
            filevardef(fout, "SPEED",typeof(ws_agl_locs),dims_3d)                           
            fout->SPEED     = (/ws_agl_locs/)
            filevarattdef(fout,"SPEED", ws_agl_locs)
        end if
        
        ; Wind direction
        r2d     = 45.0/atan(1.0)
        wd_agl_locs  = atan2(u_agl_locs, v_agl_locs) * r2d + 180.
        copy_VarMeta(v3d_template, wd_agl_locs)
        
        wd_agl_locs@description = "Wind direction"
        wd_agl_locs@units       = "degrees from North"

        if vars@direction
            filevardef(fout, "DIRECTION",typeof(wd_agl_locs),dims_3d)                           
            fout->DIRECTION = (/wd_agl_locs/)
            filevarattdef(fout,"DIRECTION", wd_agl_locs)
        end if
    end if
    
    
    ; 3D Temperature variables. If any of these are present,compute the whole lot
    if (any((/vars@t, vars@tv, vars@theta, vars@thetav, vars@rib/))) then
        
        ;temperature in kelvin
        tk          = wrf_user_getvar(file_handle, "tk", t)
        tk_agl      = wrf_user_intrp3d(tk, hgt_agl, "h", hgt_out,0, False)
        tk_agl_locs = wrf_user_hinterp(nc_file, tk_agl, lat, lon, xlat, xlong, opts@interp_option)
        
        delete(tk)
        delete(tk_agl)
        
        ; temperature in degrees C
        tc_agl_locs = tk_agl_locs - c_to_k
        copy_VarMeta(v3d_template, tc_agl_locs)
        tc_agl_locs@units = "C"
        tc_agl_locs@description = "Temperature in degrees C"


        if vars@t
            filevardef(fout, "T",typeof(tc_agl_locs),dims_3d)                         
            fout->T  = (/tc_agl_locs/) 
            filevarattdef(fout,"T", tc_agl_locs)
        end if

        
        ; water vapour mixing ratio
        qv          = wrf_user_getvar(file_handle, "QVAPOR", t)
        qv_agl      = wrf_user_intrp3d(qv, hgt_agl, "h", hgt_out,0, False) 
        qv_agl_locs = wrf_user_hinterp(nc_file, qv_agl, lat, lon, xlat, xlong, opts@interp_option)
        delete(qv)
        delete(qv_agl)

        if (isatt(vars,"qv")) .and. (vars@qv)
            filevardef(fout, "QVAPOR",typeof(qv_agl_locs),dims_3d)                           
            fout->QVAPOR     = (/qv_agl_locs/)
            filevarattdef(fout,"QVAPOR", qv_agl_locs)
        end if

        
        ;virtual temperature
        tv_agl_locs = tk_agl_locs*(1+(0.61*qv_agl_locs))
        copy_VarMeta(v3d_template, tv_agl_locs)
        tv_agl_locs@units       = "K"
        tv_agl_locs@description = "Virutal temperature"
        
        if vars@tv
            filevardef(fout, "TVIRT",typeof(tv_agl_locs),dims_3d)                           
            fout->TVIRT     = (/tv_agl_locs/) 
            filevarattdef(fout,"TVIRT", tv_agl_locs)
        end if
        
        
        ; potential temperature
        theta          = wrf_user_getvar(file_handle, "theta", t)
        theta_agl      = wrf_user_intrp3d(theta, hgt_agl, "h", hgt_out,0, False) 
        theta_agl_locs = wrf_user_hinterp(nc_file, theta_agl, lat, lon, xlat, xlong, opts@interp_option)
       
        theta_agl_locs@description = "Potential temperature"
        
        if vars@theta
            filevardef(fout, "THETA",typeof(theta_agl_locs),dims_3d)                           
            fout->THETA     = (/theta_agl_locs/)
            filevarattdef(fout,"THETA", theta_agl_locs)
        end if
        delete(theta)
        delete(theta_agl)
        
        
        ; virtual potential temperature
        thetav_agl_locs = theta_agl_locs*(1+(0.61*qv_agl_locs))
        ;delete_VarAtts(thetav_agl_locs, "description")
        ;delete_VarAtts(thetav_agl_locs, "units")

        
        thetav_agl_locs@units = "K"
        thetav_agl_locs@description = "Virtual potetial temperature"

        if vars@thetav
            filevardef(fout, "THETAV",typeof(thetav_agl_locs),dims_3d)                           
            fout->THETAV     = (/thetav_agl_locs/)
            filevarattdef(fout,"THETAV", thetav_agl_locs)
        end if
        
    end if
    
    
    ;*********************************************
    ; Bulk richardson number
    ;
    ; Jesper's method was compute Rib between two set
    ; upper and lower indices
    ; I will compute it between two specified heights
    ; set by opt@rib_lower and  opt@rib_upper
    ;
    ; Jespers code:
    ;    delta_teta_v =teta_v_profile(i,h_idx_upper,:,:)-teta_v_profile(i,h_idx_lower,:,:)
    ;    delta_u      = uu_profile(i,h_idx_upper,:,:)-uu_profile(i,h_idx_lower,:,:)
    ;    delta_v         = vv_profile(i,h_idx_upper,:,:)-vv_profile(i,h_idx_lower,:,:)
    ;    wspd_R_b         = sqrt(uu_profile(i,h_idx_R_b_type_2_h,:,:)^2+vv_profile(i,h_idx_R_b_type_2_h,:,:)^2) 
    ;    if R_b_type.eq.1 then
    ;        R_b_nr(i,:,:)=((g/dim_avg_n(t_v_profile(i,h_idx_lower:h_idx_upper,:,:),0))*delta_teta_v*delta_z)/  \
    ;                               ((delta_u^2)+(delta_v^2))
    ;    else if R_b_type.eq.2 then
    ;        R_b_nr(i,:,:)=((g/t_v_profile(i,h_idx_R_b_type_2_h,:,:))*delta_teta_v*delta_z)/  \
    ;        wspd_R_b^2
    ;    end if
    ;    end if
    ;**********************************************
    

    if vars@rib
        
        ; compute bulk richardson as difference between level i_upper and i_lower
        rib_i_upper = opts@rib_i_upper
        rib_i_lower = opts@rib_i_lower
        rib_h_upper = hgt_out(rib_i_upper)
        rib_h_lower = hgt_out(rib_i_lower)
        
        dtheta_v = thetav_agl_locs(:, :,rib_i_upper) - thetav_agl_locs(:, :, rib_i_lower)
        dspeed   = ws_agl_locs(:, :, rib_i_upper) - ws_agl_locs(:, :, rib_i_lower)

        ; What is the definition of Bulk Richardson in the case where wind speed and thetav is 
        ; the same between two levels? The equation would imply it tends to infinity, 
        ; which makes sense, this this would imply extreme stability, and you can't have turbulence
        ; generated from one layer.
        
        ; AMS method. Take virtual temperature from top layer
        if (opts@rib_opt .eq. 1)
            beta     = g/tv_agl_locs(:, :, rib_i_upper)
        
        ; Zilankavitch. Average virtual temperature over profile between layers
        else
            beta = g/dim_avg_n(thetav_agl_locs(:, :, rib_i_lower:rib_i_upper), 2)
        end if
        
        ; mask speed where the difference is very small 
        dspeed = where(dspeed.lt.0.0001, default_fillvalue("float"), dspeed)
        printVarSummary(beta)
        printVarSummary(dspeed)
        printVarSummary(dtheta_v)
        
        rib_agl_locs   = beta * dtheta_v * (rib_h_upper - rib_h_lower) / dspeed^2

        
        delete(dtheta_v)
        delete(dspeed)
        delete(beta)

        rib_agl_locs@description  = "Bulk richardson number between height_upper and height_lower using option" + sprinti("%0.1i", opts@rib_opt)
        rib_agl_locs@rib_option   = opts@rib_opt
        rib_agl_locs@height_upper = rib_h_upper
        rib_agl_locs@height_lower = rib_h_lower
        rib_agl_locs@units        = "dimensionless"
        copy_VarMeta(v2d_template, rib_agl_locs)
        filevardef(fout, "RIB",typeof(rib_agl_locs),dims_2d)                           
        fout->RIB     = (/rib_agl_locs/) 
        filevarattdef(fout,"RIB", rib_agl_locs)
    end if
   

    
    if vars@rain
        rainc  = wrf_user_getvar(file_handle, "RAINC", t) 
        rainnc = wrf_user_getvar(file_handle, "RAINNC", t) 
        rain   = rainc+rainnc
        rain_sfc_locs = wrf_user_hinterp(nc_file, rain, lat, lon, xlat, xlong, opts@interp_option)
        ;printVarSummary(rain_sfc_locs)
    
        ; Convert to rain to accumulation per hour
        do n=1,ntime-2
            k = ntime-n
            rain_sfc_locs(k, :) = rain_sfc_locs(k,:)-rain_sfc_locs(k-1,:)
        end do
        
        copy_VarMeta(v2d_template, rain_sfc_locs)
        rain_sfc_locs@height = 0
        delete_VarAtts(rain_sfc_locs, "description")
        delete_VarAtts(rain_sfc_locs, "units")
        rain_sfc_locs@description = "precipitation rate"
        rain_sfc_locs@units       = "mm/hour"
        filevardef(fout, "RAIN",typeof(rain_sfc_locs),dims_2d)                           
        fout->RAIN     = (/rain_sfc_locs/) 
        filevarattdef(fout,"RAIN", rain_sfc_locs)
    end if
    
    if vars@pblh
        pblh          = wrf_user_getvar(file_handle, "PBLH", t)
        pblh_sfc_locs = wrf_user_hinterp(nc_file, pblh, lat, lon, xlat, xlong, opts@interp_option)
        pblh_sfc_locs@height = 0
        filevardef(fout, "PBLH",typeof(pblh_sfc_locs),dims_2d)                           
        fout->PBLH     = (/pblh_sfc_locs/) 
        filevarattdef(fout,"PBLH", pblh_sfc_locs)
        delete(pblh)
        delete(pblh_sfc_locs)
    end if

    if vars@t2 then
        t2            = wrf_user_getvar(file_handle, "T2", t)
        t2c_sfc_locs  = wrf_user_hinterp(nc_file, t2, lat, lon, xlat, xlong, opts@interp_option) - c_to_k
        
        t2c_sfc_locs@height  = 2
        t2c_sfc_locs@units   = "C"
        t2c_sfc_locs@description   = "2M TEMPERATURE"
        filevardef(fout, "T2",typeof(t2c_sfc_locs),dims_2d)                           
        fout->T2     = (/t2c_sfc_locs/) 
        filevarattdef(fout,"T2", t2c_sfc_locs)
        delete(t2)
    end if

    if vars@td2 then
        td2          = wrf_user_getvar(file_handle, "td2", t)
        td2_sfc_locs = wrf_user_hinterp(nc_file, td2, lat, lon, xlat, xlong, opts@interp_option)
        td2_sfc_locs@height  = 2
        td2_sfc_locs@units   = "C"
        td2_sfc_locs@description   = "2M DEPOINT TEMPERATURE"
        filevardef(fout, "TD2",typeof(td2_sfc_locs),dims_2d)                           
        fout->TD2     = (/td2_sfc_locs/) 
        filevarattdef(fout,"TD2", td2_sfc_locs)
        delete(td2)
    end if

    
    if vars@ust then
        ust          = wrf_user_getvar(file_handle, "UST", t)
        ust_sfc_locs = wrf_user_hinterp(nc_file, ust, lat, lon, xlat, xlong, opts@interp_option)
        ust_sfc_locs@varname = "UST"
        ust_sfc_locs@height = 0
        filevardef(fout, "UST",typeof(ust_sfc_locs),dims_2d)                           
        fout->UST     = (/ust_sfc_locs/) 
        filevarattdef(fout,"UST", ust_sfc_locs)
        delete(ust)
    end if

    if vars@hfx then
        hfx          = wrf_user_getvar(file_handle, "HFX", t)
        hfx_sfc_locs = wrf_user_hinterp(nc_file, hfx, lat, lon, xlat, xlong, opts@interp_option)
        hfx_sfc_locs@varname = "HFX"
        hfx_sfc_locs@height = 0
        filevardef(fout, "HFX",typeof(hfx_sfc_locs),dims_2d)                           
        fout->HFX    = (/hfx_sfc_locs/) 
        filevarattdef(fout,"HFX", hfx_sfc_locs)
        delete(hfx)
    end if

    if vars@psfc then
        psfc          = wrf_user_getvar(file_handle, "PSFC", t)
        psfc_sfc_locs = wrf_user_hinterp(nc_file, psfc, lat, lon, xlat, xlong, opts@interp_option)
        psfc_sfc_locs@varname = "PSFC"
        psfc_sfc_locs@height = 0
        filevardef(fout, "PSFC",typeof(psfc_sfc_locs),dims_2d)                           
        fout->PSFC     = (/psfc_sfc_locs/) 
        filevarattdef(fout,"PSFC", psfc_sfc_locs)
        delete(psfc)
    end if

    if vars@sst then
        sst          = wrf_user_getvar(file_handle, "SST", t)
        sst_sfc_locs = wrf_user_hinterp(nc_file, sst, lat, lon, xlat, xlong, opts@interp_option) - c_to_k
        sst_sfc_locs@varname = "SST"
        sst_sfc_locs@height = 0
        sst_sfc_locs@units = "C"
        sst_sfc_locs@description = "SEA SURFACE TEMPERATURE"
        filevardef(fout, "SST",typeof(sst_sfc_locs),dims_2d)                           
        fout->SST     = (/sst_sfc_locs/) 
        filevarattdef(fout,"SST", sst_sfc_locs)
        delete(sst)
    end if

    if vars@tsk then
        tsk          = wrf_user_getvar(file_handle, "TSK", t)
        tsk_sfc_locs = wrf_user_hinterp(nc_file, tsk, lat, lon, xlat, xlong, opts@interp_option)
        tsk_sfc_locs@height = 0
        tsk_sfc_locs@units  = tsk@units
        filevardef(fout, "TSK",typeof(tsk_sfc_locs),dims_2d)                           
        fout->TSK     = (/tsk_sfc_locs/) 
        filevarattdef(fout,"TSK", tsk_sfc_locs)
        delete(tsk)
    end if
    
   
    if vars@swdown then
        swdown  = wrf_user_getvar(file_handle, "SWDOWN", t)
        swdown_sfc_locs = wrf_user_hinterp(nc_file, swdown, lat, lon, xlat, xlong, opts@interp_option)
        swdown_sfc_locs@height  = 0
        filevardef(fout, "SWDOWN",typeof(swdown_sfc_locs),dims_2d)                           
        fout->SWDOWN     = (/swdown_sfc_locs/) 
        filevarattdef(fout,"SWDOWN", swdown_sfc_locs)
        delete(swdown)
    end if

    if any((/vars@cldfraavg, vars@cldframax/)) then
        cldfra             = wrf_user_getvar(file_handle, "CLDFRA", t)
        cldfra_locs        = wrf_user_hinterp(nc_file, cldfra, lat, lon, xlat, xlong, opts@interp_option)

        cldfraavg_sfc_locs = dim_avg_n_Wrap(cldfra_locs, 2)
        cldframax_sfc_locs = dim_max_n(cldfra_locs, 2)
        copy_VarMeta(cldfra_locs, cldframax_sfc_locs)
        cldfraavg_sfc_locs@height = 0
        cldfraavg_sfc_locs@description = "CLOUD FRACTION COLUMN AVG"
        cldframax_sfc_locs@height = 0
        cldframax_sfc_locs@description = "CLOUD FRACTION COLUMN MAX"
        
        delete(cldfra)
        if vars@cldfraavg
            filevardef(fout, "CLDFRAAVG",typeof(cldfraavg_sfc_locs),dims_2d)                           
            fout->CLDFRAAVG   = (/cldfraavg_sfc_locs/) 
            filevarattdef(fout,"CLDFRAAVG", cldfraavg_sfc_locs)
        end if
        if vars@cldframax
            filevardef(fout, "CLDFRAMAX",typeof(cldframax_sfc_locs),dims_2d)                           
            fout->CLDFRAMAX     = (/cldframax_sfc_locs/) 
            filevarattdef(fout,"CLDFRAMAX", cldframax_sfc_locs)
        end if
    delete(cldfraavg_sfc_locs)
    delete(cldframax_sfc_locs)
    end if


    return(fout)
    
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
        height      = vars&height
        locations = vars&location
        loc_names = vars@loc_names
        lat       = vars@lat
        lon       = vars@lon
        
        nlocs   = dims(0)
        ntimes  = dims(1)
        nheight   = dims(2)
        
        do n=0,nlocs<1,1
            do k=0, nheight-1,1
                series = vars(n,:,k)
                ihgt = floattoint(height(k))
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
