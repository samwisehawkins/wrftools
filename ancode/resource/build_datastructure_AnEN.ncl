load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
load "functions_ncl/jepn_functions.ncl"
load "functions_ncl/my_functions.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl" 
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl" 

begin
test=True
; doing forecasting or reanalysis 
	forecast_mode=0
	reanalysis_mode=1
	wrf_file_post_fix=":00:00"
; diri=  getenv(web_in)
; diro= getenv(web_out)
; domain = getenv("DOMAIN")
; File = getenv("FILENAME")
; run_hour = getenv("run_hour")
   home= getenv("HOME")
; set heights for interpolations 
  h_interpolate=(/25,60,80,100,120,140,160,180 /)
  h_idx_upper=3
  h_idx_lower=0
  h_idx_R_b_type_2_h=3
  radians_per_degree  = 4.*atan(1.0)/180.

 ;R_b_type=1 ; AMS versions 
	R_b_type =2 ; Zilintikivich et all 

; define constants 

	R=287.058
	g=9.81
	cp=1003.5
	lv= 2400000 ; latent heat of evaporation 

;for testing to be removed 

	diro      = home+ "/work/An_En_RA/Input/"
;	diri      ="/Volumes/WRF_DART/Resource_assesment_work/Initial_predictions/WRF_EU2008"
	diri      ="/Volumes/WRF_DART/Resource_assesment_work/Initial_predictions/test"
	diri      ="/longbackup/jepn/reanalysis_data/EU2008"

	diri_obs  =home + "/work/An_En_RA/obs/Ray_windfarm"
	obs_prefix ="GOW" 
	obs_postfix ="no_headers"
	domain  = 2 
	run_hour= 00
;	site ="East Anglia 1"
	site="Ray_Wind_Farm"
;outfile stuff

	delimiter="  "
	file_out_prefix="AN_EN_RA"
	file_out_postfix=str_sub_str(site, " ", "_")
	file_out=diro+file_out_prefix+"_"+file_out_postfix
	system("mkdir -p diro")
	print("outputting to :"+file_out)

;remove until here 

;first read the obs - there are the key to any analog ensemble

;cancanate all files to one big 
        ncol =14
	system ("cd "+diri_obs)
	system(diri_obs+"/remove_heders_in_obs.sh")
        system ("cd "+ diri_obs+" ; cat *."+obs_postfix+ "> "+diri_obs+"/"+"OBS_cat_file."+obs_postfix)
        nrows= numAsciiRow(diri_obs+"/"+"OBS_cat_file."+obs_postfix)   ; contributed.ncl
        ncols = numAsciiCol(diri_obs+"/"+"OBS_cat_file."+obs_postfix)
        print("nrows: "+nrows)
        print("ncols"+ncols)
;read the obs
        obs  = asciiread(diri_obs+"/"+"OBS_cat_file."+obs_postfix,(/nrows,ncols/),"float")
; get the dates 
        obs_date_str=new((/nrows/),string)
        obs_date_int=new((/nrows/),integer)
	obs_date_frac=new((/nrows/),float)
	do i=0,nrows-1; numner of observations 
;       	str=(/sprinti("%0.4i",floattointeger(obs(i,0))),sprinti("%0.2i",floattointeger(obs(i,1))),sprinti("%0.2i",floattointeger(obs(i,2))),sprinti("%0.2i",floattointeger(obs(i,3))),sprinti("%0.2i",floattointeger(obs(i,4)))/)
        	str=(/sprinti("%0.4i",floattointeger(obs(i,0))),sprinti("%0.2i",floattointeger(obs(i,1))),\
        	sprinti("%0.2i",floattointeger(obs(i,2))),sprinti("%0.2i",floattointeger(obs(i,3))),sprinti("%0.2i",floattointeger(obs(i,4)))/)
        	obs_date_str(i)=str_concat(str)
        	;date_int(i)=stringtolong(date_str)
        	if mod(i,5000).eq.0 then
                	print("date:"+obs_date_str(i)+" idx: "+i)
        	end if
        		dummy=stringtochar(obs_date_str(i))
        	if dummy(10:11).eq."00" then
                	obs_date_int(i)=stringtoint(chartostring(dummy(0:9)))
                	;print("obs date:"+obs_date_int(i))
			if (obs_date_int(i).gt.1999010101 .and. obs_date_int(i).lt.2020010100)   then
				obs_date_frac(i)=yyyymmddhh_to_yyyyfrac(obs_date_int(i),0)
			end if
			;print("j:"+j+" :obsfrac "+sprintf("%5.7f",obs_date_frac(j)))
        	end if
	delete(dummy)
	end do
;print("fracs"+obs_date_frac+" ints:"+obs_date_int)
; now operate on all the initial predictions 

 File =  diri+"/wrfout_d0"+domain+"_2001-12-06_00.nc"
 print("Reading file "+File)
 f_h = addfile(File,"r")
;reads from location.csv file in /home/jepn/forecasting/location dir 
 pos= get_lat_lon(site)
; now pos holds the value of site 
 lat=pos(0)
 lon=pos(1)
 print("lat from csv file found "+lat)
 print("lon from csv file found "+lon)
; loc  = wrf_user_latlon_to_ij(f_h, lat, lon)
	  wlat=f_h->XLAT
  	  wlon=f_h->XLONG
; Find the closest point to the site in WRF grids
          obsij=wrf_latlon_to_ij(wlat,wlon,lat,lon)
	  print(obsij)
;testing position 
	test_lat = wrf_user_getvar(f_h,"lat",0)  ; slp
	test_lon = wrf_user_getvar(f_h,"lon",0)  ; slp
	print("lat for site: "+site+" is: "+wlat(obsij(0),obsij(1)) +"and lon:"+wlon(obsij(0),obsij(1)))
; now building data structure and doing bilinear interpolation 
;First add all files 
	Files = systemfunc("ls "+diri+"/wrfout_d0"+domain+"*")
        f = addfiles(Files+".nc","r")
print("found files:"+Files)
; get the file attributes we need 
      dims = dimsizes(wlat)
      nlat = dims(0)                                ; assign # lat/lon points
      nlon = dims(1)
      cen_long = f_h@STAND_LON
      dx=f_h@DX
      dy=f_h@DY
      cen_lat=f_h@CEN_LAT
      cen_lon=f_h@CEN_LON
      true_lat1=f_h@TRUELAT1
      true_lat2=f_h@TRUELAT2
      stand_lon=f_h@STAND_LON
      mminlu=f_h@MMINLU
      num_land_cat=f_h@NUM_LAND_CAT
      map_proj=f_h@MAP_PROJ
      cone = 1.
      alpha = (wlon(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1) - cen_long)*cone*radians_per_degree
      delete(dims)        
;get number of times in files and time stamps 
        times  =f[:]->Times
        dims = dimsizes(times)
        delete(dims)
; get the init yyyy mm dd from times 
        yyyy=stringtoint(chartostring(get_year_from_time_stamps(times)))
        mm=stringtoint(chartostring(get_months_from_time_stamps(times)))
        dd=stringtoint(chartostring(get_days_from_time_stamps(times)))
        hh=stringtoint(chartostring(get_hours_from_time_stamps(times)))
        days_of_year=day_of_year(yyyy,mm,dd)
;       print("Found time stamp days and converted it to day in year:"+days_of_year)
	if reanalysis_mode.eq.1 then
		valid_yyyy	=yyyy
		valid_mm	=mm
		valid_dd	=dd
		valid_hh	=hh
		valid_min	=valid_hh
		valid_min@_FillValue = -999		
		valid_min=0
;epsZero(valid_min, 24)
	else
		; read valid times from file 
		xtime=f[:]->XTIME ; denotes minutes since simulation starts 
; we need to get both the start_date attribute from each file convert it to minutes since some reference date and then add the xtime minutes convert back to yyyymmddhh cd_calendar might be the function to do that  
	end if
; get the valid times 

; get heigts
         ter= f[:]->HGT(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1)
         PHB = f[:]->PHB(:,obsij(0):obsij(0)+1,obsij(1):obsij(1)+1)
         var= f[:]->PH(:,:,obsij(0):obsij(0)+1,obsij(1):obsij(1)+1)
         dims=dimsizes(var)
	 dims_phb=dimsizes(PHB)
         ntimes=dims(0)	 
	 nlev=dims(1)
	do n=0,ntimes-1
		do j=0,nlev-1
             		 var(n,j,:,:) = var(n,j,:,:) + PHB(j,:,:)
		end do 
        end do
        z_geopot             = wrf_user_unstagger(var,var@stagger)
	z_geopot@description = "hight above terrain from geopotential"
        z_geopot@units       = "metes"
        z                    = z_geopot
	dims = dimsizes(z_geopot)
        nlevs = dims(1)
        do n=0,ntimes-1
            do k=0,nlevs-1
              z(n,k,:,:) = z(n,k,:,:)/9.81 - ter
            end do
        end do
        delete(dims)

;extract needed variables in the 4 neiboring points 
	T     =   f[:]->T(:,:,obsij(0):obsij(0)+1,obsij(1):obsij(1)+1)
 	U     =   f[:]->U(:,:,obsij(0):obsij(0)+1,obsij(1):obsij(1)+1)
	V     =   f[:]->V(:,:,obsij(0):obsij(0)+1,obsij(1):obsij(1)+1)
	LH    =   f[:]->LH(:,obsij(0):obsij(0)+1,obsij(1):obsij(1)+1)
        QV    =  f[:]->QVAPOR(:,:,obsij(0):obsij(0)+1,obsij(1):obsij(1)+1)
;extract surface fields 
	PBLH =   f[:]->PBLH(:,obsij(0):obsij(0)+1,obsij(1):obsij(1)+1)
	T2=      f[:]->T2(:,obsij(0):obsij(0)+1,obsij(1):obsij(1)+1)
	UST=     f[:]->UST(:,obsij(0):obsij(0)+1,obsij(1):obsij(1)+1)
	HFX=     f[:]->HFX(:,obsij(0):obsij(0)+1,obsij(1):obsij(1)+1)
        PSFC=    f[:]->PSFC(:,obsij(0):obsij(0)+1,obsij(1):obsij(1)+1)
; do diagnostics 
        Teta  = T + 300.        ; potential temperature in K.
        T= Teta -((g/cp)*z)	; T is now Temperature in kelvin
	T_e=T+(lv/cp)*QV
	T_v=T*(1+(0.61*QV))
        T@description="Temperature"
   	T_e@description="Virtual Temperature"
	dims=dimsizes(T)
	log_p		=new((/dims(0),dims(1),dims(2),dims(3)/),float)
	uu		=new((/dims(0),dims(1),dims(2),dims(3)/),float)
	vv		=new((/dims(0),dims(1),dims(2),dims(3)/),float)
	R_b_nr          =new((/dims(0),dims(2),dims(3)/),float)
	nwp_valid_times	=new((/dims(0)/),string)
	data_out	=new((/dims(0)+2/),string); each line holds all variables 
 	R_b_nr_point    =new((/dims(0)/),float)

do i=0,dims(0)-1 ;time loop 
	do j=0,dims(1)-1 ; level loop
		do l=0,dims(2)-1 ;long loop
			do k=0,dims(3)-1 ;lat loop
				term_1=(Teta(i,j,l,k)/T(i,j,l,k))
		 		term_2=(R/cp)*log(PSFC(i,l,k))
				log_p(i,j,l,k)=cp/R*(term_2-term_1)
			end do
		end do 
	end do 
end do
	P=exp(log_p)
        Teta_e = wrf_eth( QV, T, P )
	Teta_v=Teta*(1+(0.61*QV)) 
	dims=dimsizes(T)
	nlev=dims(1);
	ntimes=dims(0)
     do i=0,nlevs-1
     	do n=0,ntimes-1
	      uu(n,i,:,:) = U(n,i,:,:)*cos(alpha) + V(n,i,:,:)*sin(alpha)
	      vv(n,i,:,:) = V(n,i,:,:)*cos(alpha) - U(n,i,:,:)*sin(alpha)
	end do
    end do
    wspd = sqrt(uu*uu+vv*vv)
    wdir = atan2(uu,vv)/radians_per_degree + 180.
    copy_VarMeta(uu,wspd)
    copy_VarMeta(vv,wdir)

;Interpolate to explicit heights
        uu_profile	 = wrf_user_intrp3d(uu,z,"h",h_interpolate,0.,False)
	vv_profile	 = wrf_user_intrp3d(vv,z,"h",h_interpolate,0.,False)
 	wspd_profile	 = wrf_user_intrp3d(wspd,z,"h",h_interpolate,0.,False)
        wdir_profile	 = wrf_user_intrp3d(wdir,z,"h",h_interpolate,0.,False)	
	t_profile	 = wrf_user_intrp3d(T,z,"h",h_interpolate,0.,False)
	teta_profile	 = wrf_user_intrp3d(Teta,z,"h",h_interpolate,0.,False)
	teta_e_profile	 = wrf_user_intrp3d(Teta_e,z,"h",h_interpolate,0.,False)
	teta_v_profile   = wrf_user_intrp3d(Teta_v,z,"h",h_interpolate,0.,False)
	q_profile        = wrf_user_intrp3d(QV,z,"h",h_interpolate,0.,False)
        t_e_profile      = wrf_user_intrp3d(T_e,z,"h",h_interpolate,0.,False)
	t_v_profile      = wrf_user_intrp3d(T_v,z,"h",h_interpolate,0.,False)
; biliearly interpolate to obs points
          uu_profile_point        =rcm2points(wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),uu_profile,lat,lon,1)
          vv_profile_point        = rcm2points(wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),vv_profile,lat,lon,1) 
          wspd_profile_point      = rcm2points(wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wspd_profile,lat,lon,1)
          wdir_profile_point      = rcm2points(wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wdir_profile,lat,lon,1)
          t_profile_point         = rcm2points(wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),t_profile,lat,lon,1)
          teta_profile_point      = rcm2points(wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),teta_profile,lat,lon,1)
          teta_e_profile_point    = rcm2points(wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),teta_e_profile,lat,lon,1)
          teta_v_profile_point    = rcm2points(wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),teta_v_profile,lat,lon,1)
          q_profile_point         = rcm2points(wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),q_profile,lat,lon,1)
          t_e_profile_point       = rcm2points(wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),t_e_profile,lat,lon,1)
          t_v_profile_point       = rcm2points(wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),t_v_profile,lat,lon,1)
		psfc_point	  =rcm2points(wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),PSFC,lat,lon,1)		
   		pblh_point        =rcm2points(wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),PBLH,lat,lon,1)     
	  	 t_2_point        =rcm2points(wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),T2,lat,lon,1) 
   		hfx_point        =rcm2points(wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),HFX,lat,lon,1)     	
   		ust_point        =rcm2points(wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),UST,lat,lon,1)     
;S:lSoop through all time stamps and build string matrix to be written to file txt or hdf
        ; compute Bulk Ricardson numbers   i
;header section 
	delta_z=h_interpolate(h_idx_upper)-h_interpolate(h_idx_lower)
        header_line=(/"Valid_time",delimiter,"Init_time",delimiter,"Lead_time",delimiter,"wspd_25m",delimiter,  \
	"wspd_60",delimiter,"wspd_80",delimiter,"wspd_100",delimiter,"wspd_120",delimiter, \
	"wspd_140",delimiter,"wspd_160",delimiter,"wspd_180",delimiter,"wdir_25",delimiter,"wdir_60",delimiter,"wdir_80",   \
	delimiter,"wdir_100",delimiter,"wdir_120",delimiter,"wdir_140",delimiter,"wdir_160",delimiter,"wdir_180" \
	,delimiter,"Surface_Preasure",delimiter,"PBLH",delimiter,"T_2",delimiter,"Heat_Flux",delimiter,"USTAR",delimiter,"Bulk_Richardson"  \
	,delimiter,"Observed_wspd_70_7m",delimiter,"Observed_wspd_25_4m",delimiter,"Observed_wind-direction"  /)
	data_out_string=str_concat(header_line)	
	data_out(0)=str_concat(data_out_string); add header line 
 	delete(data_out_string)	
; end header section 
	do  i=0,ntimes-1
	str=(/sprinti("%0.4i",valid_yyyy(i)),sprinti("%0.2i",valid_mm(i)),sprinti("%0.2i",valid_dd(i)),sprinti("%0.2i",valid_hh(i)),sprinti("%0.2i",valid_min(i))/)
	nwp_valid_times(i)=str_concat(str)	
	delete(str)	
	delta_teta_v =teta_v_profile(i,h_idx_upper,:,:)-teta_v_profile(i,h_idx_lower,:,:)
		delta_u      =uu_profile(i,h_idx_upper,:,:)-uu_profile(i,h_idx_lower,:,:)
		delta_v	     =vv_profile(i,h_idx_upper,:,:)-vv_profile(i,h_idx_lower,:,:)
		wspd_R_b         = sqrt(uu_profile(i,h_idx_R_b_type_2_h,:,:)^2+vv_profile(i,h_idx_R_b_type_2_h,:,:)^2) 
		if R_b_type.eq.1 then
			R_b_nr(i,:,:)=((g/dim_avg_n(t_v_profile(i,h_idx_lower:h_idx_upper,:,:),0))*delta_teta_v*delta_z)/  \
                        	        ((delta_u^2)+(delta_v^2))
		else if R_b_type.eq.2 then
			R_b_nr(i,:,:)=((g/t_v_profile(i,h_idx_R_b_type_2_h,:,:))*delta_teta_v*delta_z)/  \
			wspd_R_b^2
		end if
		end if
	R_b_nr_point(i)   = rcm2points(wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),wlat(obsij(0):obsij(0)+1,obsij(1):obsij(1)+1),R_b_nr(i,:,:),lat,lon,1)
	data_out_string=nwp_valid_times(i)+delimiter
	data_out_string=data_out_string+nwp_valid_times(i)+delimiter
	data_out_string=data_out_string+"00"+delimiter
	data_out_string=data_out_string+sprintf("%5.2f",wspd_profile_point(i,0,0))+delimiter	
	data_out_string=data_out_string+sprintf("%5.2f",wspd_profile_point(i,1,0))+delimiter
	data_out_string=data_out_string+sprintf("%5.2f",wspd_profile_point(i,2,0))+delimiter
	data_out_string=data_out_string+sprintf("%5.2f",wspd_profile_point(i,3,0))+delimiter
	data_out_string=data_out_string+sprintf("%5.2f",wspd_profile_point(i,4,0))+delimiter
	data_out_string=data_out_string+sprintf("%5.2f",wspd_profile_point(i,5,0))+delimiter
	data_out_string=data_out_string+sprintf("%5.2f",wspd_profile_point(i,6,0))+delimiter
	data_out_string=data_out_string+sprintf("%5.2f",wspd_profile_point(i,7,0))+delimiter
	data_out_string=data_out_string+sprintf("%5.1f",wdir_profile_point(i,0,0))+delimiter
        data_out_string=data_out_string+sprintf("%5.1f",wdir_profile_point(i,1,0))+delimiter
        data_out_string=data_out_string+sprintf("%5.1f",wdir_profile_point(i,2,0))+delimiter
        data_out_string=data_out_string+sprintf("%5.1f",wdir_profile_point(i,3,0))+delimiter
        data_out_string=data_out_string+sprintf("%5.1f",wdir_profile_point(i,4,0))+delimiter
        data_out_string=data_out_string+sprintf("%5.1f",wdir_profile_point(i,5,0))+delimiter
        data_out_string=data_out_string+sprintf("%5.1f",wdir_profile_point(i,6,0))+delimiter
        data_out_string=data_out_string+sprintf("%5.1f",wdir_profile_point(i,7,0))+delimiter
	data_out_string=data_out_string+sprintf("%8.1f",psfc_point(i,0))+delimiter
	data_out_string=data_out_string+sprintf("%6.1f",pblh_point(i,0))+delimiter
	data_out_string=data_out_string+sprintf("%7.3f",t_2_point(i,0))+delimiter
	data_out_string=data_out_string+sprintf("%7.3f",hfx_point(i,0))+delimiter
	data_out_string=data_out_string+sprintf("%7.3f",ust_point(i,0))+delimiter	
	data_out_string=data_out_string+sprintf("%7.3f",R_b_nr_point(i))+delimiter
	data_out(i+1)=str_concat(data_out_string)
	dummy=stringtochar(nwp_valid_times(i))
	valid_date_tempo=chartostring(dummy(0:9))
	delete(dummy)
	valid_date_frac=yyyymmddhh_to_yyyyfrac(stringtoint(valid_date_tempo),0)
	; now see if the varifying observtion exists and append it  
	obs_idx=ind(valid_date_frac.eq.obs_date_frac)	
	if all(.not.ismissing(obs_idx)) then
		print("found matching obs at posision:"+obs_idx)
   		data_out_string=data_out_string+sprintf("%6.2f",obs(obs_idx(0),6))+delimiter;wspd
		data_out_string=data_out_string+sprintf("%6.2f",obs(obs_idx(0),10))+delimiter;wspd
		data_out_string=data_out_string+sprintf("%6.2f",obs(obs_idx(0),8))+delimiter ;wdir               
 		data_out(i+1)=str_concat(data_out_string)
	else
		;No match found
		data_out_string=data_out_string+sprintf("%6.2f",-999.99)+delimiter
		data_out_string=data_out_string+sprintf("%6.2f",-999.99)+delimiter
		data_out_string=data_out_string+sprintf("%6.2f",-999.99)+delimiter          
	        data_out(i+1)=str_concat(data_out_string)
	end if 
      	delete(obs_idx)
        delete(valid_date_frac) 
	if mod(i,10000).eq.0
		asciiwrite(file_out,data_out) ; make sure to write to file along the way 
	end if 
end do ; times in initial predictions 
print("printing to: "+file_out)
asciiwrite(file_out,data_out)

nfields = str_fields_count(data_out(1),delimiter)   ; Count the fields separated
print(nfields)                               ; nfields = 20

 field =6 
 	nwp_wind_80m = stringtofloat(str_get_field(data_out, field, delimiter))
 field =26
 	obs_wind_70m = stringtofloat(str_get_field(data_out, field, delimiter))
obs_wind_70m@_FillValue=-999.99
	non_missing_idx=ind(.not.ismissing(obs_wind_70m))
print("obs winds"+obs_wind_70m+"nwp winds "+nwp_wind_80m)
print("idx"+non_missing_idx)
;plot section

;---Create new 2D array to hold groupings of values
  data2d =(/obs_wind_70m(non_missing_idx),nwp_wind_80m(non_missing_idx)/) 

;----------------------------------------------------------------------
; Graphics section
;----------------------------------------------------------------------

  colors = (/"white","black","darkgoldenrod","darkgreen","coral4", \ 
             "cyan3","firebrick1","darkslateblue","limegreen",     \
             "lightgoldenrod","darkseagreen1","lightsteelblue1"/)

  wks  = gsn_open_wks("png","U_nwp_80m_Uobs_70m")              ; specifies a ps plot
  gsn_define_colormap(wks,colors)

;---Create a scatter plot
  res                    = True                   ; plot mods desired

;---Set some legend resurces
  res@tiMainString      = "Scatter Plot"           ; add title
  res@xyMarkLineModes   = "Markers"                ; choose which have markers
  res@xyMarkers         =  16                      ; choose type of marker  
  res@xyMarkerColor     = "red"                    ; Marker color
  res@xyMarkerSizeF     = 0.01    
  res@pmLegendDisplayMode    = "Always"         ; Turn on the legend
  res@lgOrientation          = "horizontal"     ; Default is vertical
  res@pmLegendWidthF         = 0.75             ; Make it wider
  res@pmLegendOrthogonalPosF = -0.1             ; Move it up slightly
  res@lgPerimOn              = False            ; Turn off the perimeter box
  res@xyMarkerColor = "blue"
  res@tiMainString  = "Make your own marker"
  res@xyMarkers     = NhlNewMarker(wks, "^", 19, 0.0, 0.0, 1.3125, 1.5, 0.0)
  plot              = gsn_csm_xy (wks,obs_wind_70m(non_missing_idx),nwp_wind_80m(non_missing_idx),res) 
;
  plot  = gsn_csm_y (wks,data2d,res)


; compute stability distribution 
opt=True
opt@bin_max=0.4
opt@bin_min=-0.4
R_b_pdf = pdfx(R_b_nr_point,13,opt)
percent =R_b_pdf
percent = (/R_b_pdf(0),R_b_pdf(1) ,R_b_pdf(2), R_b_pdf(3),R_b_pdf(4), R_b_pdf(5), R_b_pdf(6),R_b_pdf(7),R_b_pdf(8),R_b_pdf(9),R_b_pdf(10),R_b_pdf(11),R_b_pdf(12)/)
print(percent)
 colors   = (/ "red", "green", "orange", "yellow", "brown","magenta","blue","gray" /)
; name    = (/ "Deciduous", "Savanna", "Wetland", "Tundra", "Evergreen", "Desert", "Cropland", "Grassland" /)

; pcRes   = True
print(charactertostring(times(0,:)))
 strs = (/"Site:",site,"Period:",charactertostring(times(0,:))," to ",charactertostring(times(ntimes-1,:))/)
 title_str = str_concat(strs)
 res  = True
 res@gsnDraw                = True
 res@gsnFrame               = True
 res@xyLineThicknessF       = 4
 res@xyLineColors           =(/"red"/) 
 res@tiXAxisString          = "Bulk Richardson number"
 res@tiYAxisString          = "Frequency of occurrence (%) "
 res@gsnCenterString        = title_str 
 res@trXMinF                =-0.2
 res@trXMaxF		    =0.2
 res@tmXMajorGrid                = True          ; implement x grid 
 res@tmXMajorGridThicknessF      = 1.0           ; 2.0 is default
 res@tmXMajorGridLineDashPattern = 2             ; select short dash lines
 res@tmYMajorGrid                = True          ; implement y grid
 res@tmYMajorGridThicknessF      = 1.0           ; 2.0 is default
 res@tmYMajorGridLineDashPattern = 2             ; select short dash lines
 res@xyMarkLineMode     = "Markers"
 res@xyMarkerSizeF      = 0.03
 res@xyMarkerThicknessF = 3.
  res@xyMonoMarkerColor  = False          ; Allow different colors for markers
  res@xyMarkerColors     = colors(7:)  
 wks 			    = gsn_open_wks("pdf","R_b_pdf_xy")
 plot			    = gsn_csm_xy (wks, R_b_pdf@bin_center, R_b_pdf, res)

end
