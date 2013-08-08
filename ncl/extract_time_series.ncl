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
;******************************************************

    

;******************************************************
; Constants / hard coded options
;******************************************************
  extract_heights    = (/50.,60.,70.,80.,90.,100./)
  dims    = dimsizes(extract_heights)
  nhgts = dims(0)
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
    ; Bulk richardson options
    ; Rib_opt=1 ; AMS versions 
	opts@rib_opt=2 ; Zilintikivich et al
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
;    vars@v                 = True      ;earth relative v-component               - output as V
;    vars@speed             = True      ;wind speed                               - output as SPEED
;    vars@direction         = True      ;earth-relative wind direction            - output as DIRECTION
;    vars@t                 = True      ;temperature                              - output as T
;    vars@tv                = True      ; virtual temperature                     - output as TV
;    vars@theta             = True      ;potential temperature                    - output as THETA
;    vars@thetav            = True      ;virtual potential temperature            - output as THETAV
;    vars@tke               = True      ;TKE from PBL scheme                      - output as TKE (not yet implemented)
;	vars@rib               = True      ;Bulk Richardson number                   - output as RIB
   
  ;****************************
  ; 2D (surface or averaged) variables
  ;****************************
;  vars@sst               = True      ;sea-surface temperature                  - output as SST
  vars@tsk               = False     ;skin (surface) temperature               - output as TSK
;  vars@t2                = True      ;temperature at 2m                        - output as T2
;  vars@td2               = True      ;dewpoint temperature at 2m               - output as TD2
  vars@theta2            = False     ;potential temperature at 2m              - not yet implemented
  vars@psfc              = False     ;pressure at the surface                  - not yet implemented
  vars@slp               = False     ;sea-level pressure- using WRF-NCL        - not yet implemented
  vars@tsfc              = False     ;temperature at the surface               - not yet implemented
  vars@rv2               = False     ;mixing ratio at 2m                       - not yet implemented
  vars@q2                = False     ;specific humidity at 2m                  - not yet implemented
  vars@rh2               = False     ;relative humidity at 2m                  - not yet implemented
  vars@u10               = False     ;u wind - grid - at 10m                   - not yet implemented
  vars@v10               = False     ;v wind - grid - at 10m                   - not yet implemented
  vars@ws_10             = False     ;wind speed - at 10m                      - not yet implemented
  vars@wd_10             = False     ;wind direction - earth - at 10m          - not yet implemented
;  vars@rain              = True      ;total grid scale precipitation           - output as RAIN
  vars@precip_c          = False     ;total cumulus precipitation              - not yet implemented
  vars@precip_fr         = False     ;fraction of frozen nonconv. precip       - not yet implemented
  vars@dryairmass        = False     ;total dry air mass in column             - not yet implemented
  vars@pblh              = False     ;PBL height                               - not yet implemented
  vars@rho               = False     ;density at lowest eta level              - not yet implemented
;  vars@swdown            = True      ;downward short wave flux at ground surface -- output as SWDOWN
;  vars@cldfraavg         = True      ;cloud fraction column average              -- output as CLDFRAAVG
;  vars@cldframax         = True      ;cloud fraction column maximun              -- output as CLDFRAMAX
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
	
	dims = dimsizes(output)
	nvars = dims(0)
	delete(dims)

	do i=0,nvars-1
	    output[i]&location   = loc_id
	    output[i]@domain     = domain
        output[i]@model      = "WRF"
        output[i]@model_run  = model_run
        output[i]@nest_id    = f@GRID_ID
		output[i]@init_time  = init_time
	end do
    
	;******************************************************
    ; Output vars to ASCII file
    ;******************************************************
	us = inttochar(95) ; underscore
	do i=0,nvars-1
		var = output[i]
		printVarSummary(var)
		dims = dimsizes(var)
		ddims = dimsizes(dims)
		ndims = ddims(0)
		print(ndims)
		delete(dims)
		delete(ddims)
        
		; 3D variable	    
		if (ndims .eq. 3)
	        do n=0,nlocs<1,1
		        do k=0, nhgts-1,1
			        series = var(n,:,k)
					; ensure height is three digit integer
					ihgt = floattoint(series@height)
                    shgt = sprinti("%0.3i", ihgt)
   				
                    series@lat      = lat(n)
                    series@lon      = lon(n)
				    printVarSummary(series)
					
				    fname   = out_dir + "/" +\
                         series@location + us +\
                         series@var_name + us +\
						 "d" + sprinti("%0.2i", series@nest_id)+ us +\
						 shgt+ us +\
                         series@init_time +".txt"
                    print(fname)
					
				    write_series(series, fname)
					
					delete(series)
					delete(fname)
					delete(ihgt)
					delete(shgt)
		        end do
			end do
		end if
        
		; 2D Var
		if (ndims .eq. 2)
	        do n=0,nlocs<1,1
		        series = var(n,:)
				; ensure height is three digit integer
				;ihgt = floattoint(series@height)
				;shgt = sprinti("%0.3i", ihgt)
   				
				series@lat      = lat(n)
				series@lon      = lon(n)
				printVarSummary(series)
					
				fname   = out_dir + "/" +\
					 series@location + us +\
					 series@var_name + us + "d" +\
					 sprinti("%0.2i", series@nest_id) + us +\
				     series@init_time +".txt"
				print(fname)
					
				write_series(series, fname)
					
				delete(series)
				delete(fname)

			end do
		end if
		
		delete(var)
	end do
	
	
	exit






	
    ;******************************************************
    ; File naming, headers
    ;
    ; To be consistent with existing code, files should be 
    ; named like: SLG_VGRD_d01_100_2012-11-17_12.txt
    ; where: SLG  = location_id
    ;          VGRD = 'standard' variable name
    ;          d01  = nest_id
    ;          100  = height above surface, integer 3-digits
    ; 2012-11-17_12 = fcst initial time  
    ;******************************************************

    header = (/"domain","model_run","model","nest_id","location_id","latitude","longitude","variable","init_time","valid_time","height","value"/)



print("*** SUCCESS NCL EXTRACT TIME SERIES ***")

end
