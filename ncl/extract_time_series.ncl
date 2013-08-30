;******************************************************
; Extract time-series from WRF netcdf files write output 
; to a simple text file. 
;
; Credit to Dennis Shea's wrfout_to_cf.ncl for some inspiration
;
;
; Author Sam Hawkins, Jesper Nissen
; sam.hawkins@vattenfall.com
; 
;******************************************************
load "$HOME/code/wrftools/devel/ncl/wrftools.ncl"

begin

;******************************************************
; Environment variables used by this script
;******************************************************
  in_file   = getenv("NCL_IN_FILE")    ; this can be a pattern, and will be expanded by systemfunc(ls)
  out_dir   = getenv("NCL_OUT_DIR")
  nest_id   = getenv("NEST_ID")    
  loc_file  = getenv("LOCATIONS_FILE")
  domain    = getenv("DOMAIN")        ; these will get used as metatdata
  model_run = getenv("MODEL_RUN")     ; these will get used as metatdata
  grid_id   = stringtointeger(getenv("GRID_ID"))       ; this may get read from global attribute
  ;******************************************************

    

;******************************************************
; Constants / hard coded options
;******************************************************
  extract_heights    = (/50.,60.,70.,80.,90.,100./)
  dims    = dimsizes(extract_heights)
  nhgts   = dims(0)
  delete(dims)
;******************************************************



;******************************************************
; Options
  opts = True
;******************************************************  
    ;**************************************************
    ; Horizontal interpolation options
    ; 0: none, use grid cell value from wrf_user_ll_to_ij (not implemented yet!)
    ; 1: inverse distance weighting as implemented by rcm2points(opt=1)
    ; 2: bilinear interpolation as implemented by rcm2points(opt=2)
    ;**************************************************
    opts@interp_option = 0

    ;**************************************************
    ; Latitude/longitude options
    ; 0 lat(time, south_north, west_east)
    ; 1 lat(south_north, west_east)
	opts@latlon=1 
    ;**************************************************

    ;**************************************************
    ; Reduced WRF output from Riso dataset
    ; 0 full wrf output
    ; 1 reduced WRF output
	opts@reduced = True
    ;**************************************************

    
    ;**************************************************
    ; Bulk richardson options
    ; Rib_opt=1        ; AMS versions 
	opts@rib_opt=2     ; Zilintikivich et al
    opts@rib_l = 10    ; lower height
    opts@rib_u = 40    ; upper height
    ;**************************************************

;******************************************************  


;******************************************************
; Output Variables
;******************************************************
    
    ;****************************************************
    ; 3D variables 
    ;****************************************************
    vars = True
    vars@u                 = True      ;earth relative u-component               - output as U 
    vars@v                 = True      ;earth relative v-component               - output as V
    vars@speed             = True      ;wind speed                               - output as SPEED
    vars@direction         = True      ;earth-relative wind direction            - output as DIRECTION
    vars@t                 = True      ;temperature                              - output as T
    vars@tv                = True      ;virtual temperature                      - output as TV
    vars@theta             = True      ;potential temperature                    - output as THETA
    vars@thetav            = True      ;virtual potential temperature            - output as THETAV
    vars@tke               = True      ;TKE from PBL scheme                      - output as TKE (not yet implemented)
	vars@rib               = True      ;Bulk Richardson number                   - output as RIB
   
  ;****************************
  ; 2D (surface or averaged) variables
  ;****************************
  vars@sst               = True      ;sea-surface temperature                  - output as SST
  vars@tsk               = False     ;skin (surface) temperature               - output as TSK
  vars@t2                = True      ;temperature at 2m                        - output as T2
  vars@td2               = True      ;dewpoint temperature at 2m               - output as TD2
  vars@pblh              = True      ;PBL height                               - output as PBLH
  vars@psfc              = True      ;pressure at the surface                  - output as PSFC  
  vars@swdown            = True      ;downward short wave flux at ground surface -- output as SWDOWN
  vars@cldfraavg         = False      ;cloud fraction column average              -- output as CLDFRAAVG
  vars@cldframax         = False      ;cloud fraction column maximun              -- output as CLDFRAMAX
  vars@rain              = True      ;total grid scale precipitation           - output as RAIN
  vars@slp               = True     ;sea-level pressure- using WRF-NCL        - not yet implemented

  
  vars@theta2            = False     ;potential temperature at 2m              - not yet implemented
  vars@ust               = False     ;friction velocity ust at surface         - not yet implemented
  vars@hfx               = False     ;surface heat flux                        - not yet implemented

  vars@tsfc              = False     ;temperature at the surface               - not yet implemented
  vars@rv2               = False     ;mixing ratio at 2m                       - not yet implemented
  vars@q2                = False     ;specific humidity at 2m                  - not yet implemented
  vars@rh2               = False     ;relative humidity at 2m                  - not yet implemented
  vars@u10               = False     ;u wind - grid - at 10m                   - not yet implemented
  vars@v10               = False     ;v wind - grid - at 10m                   - not yet implemented
  vars@ws_10             = False     ;wind speed - at 10m                      - not yet implemented
  vars@wd_10             = False     ;wind direction - earth - at 10m          - not yet implemented

  vars@precip_c          = False     ;total cumulus precipitation              - not yet implemented
  vars@precip_fr         = False     ;fraction of frozen nonconv. precip       - not yet implemented
  vars@dryairmass        = False     ;total dry air mass in column             - not yet implemented
  vars@rho               = False     ;density at lowest eta level              - not yet implemented
  

;******************************************************


;******************************************************
; Give some info
;******************************************************
print("NCL Extracting time series from file(s): "+in_file)


;******************************************************
; Add the file(s)
; Only used addfiles if there is more than one file
;******************************************************
    files = systemfunc("ls "+in_file)
    print(files)
	dims = dimsizes(files)
    nfiles = dims(0)
    delete(dims)
  
    if (nfiles.eq.1) then 
        f = addfile(files(0)+".nc","r")
    else 
        f = addfiles(files+"nc", "r")
    end if 
  
 
    locations = read_locations(loc_file)
    loc_id = locations[0]
	name   = locations[1]
	lat    = locations[2]
	lon    = locations[3]
	
    print(loc_id)
    dims=dimsizes(loc_id)
    nlocs = dims(0)
    delete(dims)	

    print("Read " + nlocs+ " locations from file: " + loc_file)
    output = wrf_user_interp_vars(f, extract_heights, lat, lon,-1, vars, opts)

    nvars = ListCount(output)
	do i=0,nvars-1
        print(output[i]@varname)
	end do


	;******************************************************
    ; Get times and dimensions
    ;******************************************************
    times     = f->Times
    ud_times  = wrf_times_c(times, 0)             ; should be same as below
	fcst_hrs  = WRF_Times_to_udunits(times, 0)    ; using 0 forces the units to be hours since first time in the file
    init_time = chartostring(times(0,0:12))
    dims = dimsizes(fcst_hrs)
    ntimes=dims(0)
    delete(dims)

	;******************************************************
    ; Add metadata to output vars
    ;******************************************************
	do i=0,nvars-1
        print(output[i]@varname)
        printVarSummary(output[i])
        output[i]&location   = loc_id
	    output[i]@domain     = domain
        output[i]@model      = "WRF"
        output[i]@model_run  = model_run
        ;output[i]@nest_id    = f@GRID_ID
		printVarSummary(grid_id)
        output[i]@nest_id    = grid_id
        output[i]@init_time  = init_time
	end do
    
	;******************************************************
    ; Output vars to ASCII file
    ;******************************************************
	us = inttochar(95) ; underscore
	
    print("Outputting nvars: " + sprinti("%0.1i", nvars))
    print(nvars)
    do i=0,nvars-1
		var = output[i]
		print(var@varname)
		dims = dimsizes(var)
		ddims = dimsizes(dims)
		ndims = ddims(0)
		print(ndims)
		delete(dims)
		delete(ddims)
        
		; 3D variable	    
		if (ndims .eq. 3)
	        print("3D variable")
            do n=0,nlocs<1,1
		        do k=0, nhgts-1,1
			        series = var(n,:,k)
					; ensure height is three digit integer
					ihgt = floattoint(series@height)
                    shgt = sprinti("%0.3i", ihgt)
   				    dom  = stringtointeger(series@nest_id)
                    series@lat      = lat(n)
                    series@lon      = lon(n)
				    printVarSummary(series)
                    print(series@nest_id)										
				    fname   = out_dir + "/" +\
                         series@location + us +\
                         series@varname + us +\
						 "d" + sprinti("%0.2i", dom) + us +\
						 shgt+ us +\
                         series@init_time +".txt"
				
				    write_series(series, fname)
					
					delete(series)
					delete(fname)
					delete(ihgt)
					delete(shgt)
                    delete(dom)
		        end do
			end do
		end if
        
		; 2D Var
		if (ndims .eq. 2)
	        print("2D variable")
            do n=0,nlocs<1,1
		        series = var(n,:)
				; ensure height is three digit integer
				;ihgt = floattoint(series@height)
				;shgt = sprinti("%0.3i", ihgt)
   				dom  = stringtointeger(series@nest_id)
				series@lat      = lat(n)
				series@lon      = lon(n)
				fname   = out_dir + "/" +\
					 series@location + us +\
					 series@varname + us + "d" +\
					 sprinti("%0.2i", dom) + us +\
				     series@init_time +".txt"
				print(fname)
					
				write_series(series, fname)
					
				delete(series)
				delete(fname)
                delete(dom)

			end do
		end if
		
		delete(var)
	end do
	
	
print("*** SUCCESS NCL EXTRACT TIME SERIES ***")

end
