function get_year_from_time_stamps(times)
begin

return times(:,0:3) 
end 



function get_months_from_time_stamps(times)
begin

return times(:,5:6)
end


function get_days_from_time_stamps(times)
begin

return times(:,8:9)
end


function get_hours_from_time_stamps(times)
begin

return times(:,11:12)
end

function get_number_of_days_in_dd(dd,hh)
	begin
	dims=dimsizes(dd)
	print("dims er "+dims)
start_day=dd(0)
num_of_different_days=1
print("first day is :"+start_day)
		do i=0,dims(0)-1
			if(start_day.ne.dd(i))
				num_of_different_days=num_of_different_days+1
				start_day=dd(i)
			end if
		end do
; tjeck if last day is only the 00:00
		if (hh(dims-1).eq.0)then
			return  num_of_different_days-1
		else
		return num_of_different_days
		end if
	end

function detect_missing_days(files)

begin
char_file_names=stringtochar(files)
int_day=stringtointeger(chartostring(char_file_names(:,60:62)))
j=0
n=0
dims=dimsizes(char_file_names)
num_days =dims(0)
num_letters_in_file_name=dims(1)
print("found number of days:"+num_days)

if ((num_days.eq.365).or.(num_days.eq.366)) then
        return 0
else ; find the missing days
       num_missing_days=365-num_days 
       missing_days=new((/num_missing_days/),integer) ; get the missing days
        do i=1,365
                if(i.eq.int_day(j)) then
        ;                print("filename_day is:"+int_day(j)+" i is:"+i)
			if (j.eq.num_days-1) then ;all days compared
				return missing_days(ind(.not.ismissing(missing_days)))	
			else
                        	j=j+1
;				print("j is:"+j)
			end if
                else
                        ; print("Missing day is :"+i)
                         missing_days(n)=i
 			 n=n+1

                end if
        end do
        return missing_days 
end if


;print("from missing days:"+char_file_names(:,60:62))
end

function set_res(ff,year)
begin
res                    = True                    ; plot mods desired

  res@tiMainString  = year   ; Main title
  res@cnLinesOn          = False 
  res@cnFillOn           = True               ; color plot desired
  res@cnLineLabelsOn     = False              ; turn off contour lines
  res@mpDataBaseVersion  = "Ncarg4_1" ; higher res data base
  res@mpProjection        = "Stereographic"
  res@mpCenterLonF        = ff@CEN_LON 
  res@mpCenterLatF        = 90;ff@CEN_LAT
  res@mpLimitMode        = "Corners" ; choose range of map
  res@tfDoNDCOverlay     = True
  res@gsnSpreadColors    = True             ; use full range of colormap
  res@gsnAddCyclic = False
  res@gsnMaximize = True

  res@cnLevelSelectionMode = "ManualLevels"        ; set manual contour levels
  res@cnMinLevelValF       =  4.                 ; set min contour level
  res@cnMaxLevelValF       =  12.                  ; set max contour level
  res@cnLevelSpacingF      =  .5                  ; set contour spacing
  res@gsnAddCyclic = False

  xlat = ff->XLAT
  xlon = ff->XLONG
  dims = dimsizes(xlat)
  nlat = dims(0)                                ; assign # lat/lon points
  nlon = dims(1)
  res@mpLeftCornerLatF  = xlat(0,0)
  res@mpLeftCornerLonF  = xlon(0,0)
  res@mpRightCornerLatF = xlat(nlat-1,nlon-1)
  res@mpRightCornerLonF = xlon(nlat-1,nlon-1)
  res@mpPerimOn          = True ; draw box around map
  res@mpPerimDrawOrder   = "PostDraw"

; label bar section
	res@lbLabelBarOn        = False           ; turn off individual cb's



return res 
end
