load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
load "/home/jepn/work/web_forecast/functions/jepn_functions.ncl"

begin
 wrf_file_post_fix=":00:00"
; diri=  getenv(web_in)
; diro= getenv(web_out)
; domain = getenv("DOMAIN")
; File = getenv("FILENAME")
; run_hour = getenv("run_hour")

;for testing to be removed 
 diro="/home/jepn/work/web/html/NSeaWRF_VWPP"
 diri="/home/jepn/forecasting/domains/Thannet/operational/wrfout"
 domain = 3 
 run_hour = 00
 site ="East Anglia 1"
;remove until here 
 File =  diri+"/wrfout_d0"+domain+"_2013-04-22_00:00:00.nc"
 print("Reading file "+File)
 f_h = addfile(File,"r")
print(f_h)
;reads from location.csv file in /home/jepn/forecasting/location dir 
 pos= get_lat_lon(site)
; now pos holds the value of site 
 lat=pos(0)
 lon=pos(1)
 print("lat from csv file found "+lat)
 print("lon from csv file found "+lon)
 loc  = wrf_user_latlon_to_ij(f_h, lat, lon)
;testing position 
	test_lat = wrf_user_getvar(f_h,"lat",0)  ; slp
	test_lon = wrf_user_getvar(f_h,"lon",0)  ; slp
	print("lat for site: "+site+" is: "+test_lat(loc(0),loc(1))+" and lon:"+test_lon(loc(0),loc(1)))

; now doing bilinear interpolation 
end
