load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"
load "functions/jepn_functions.ncl"
load "functions/my_functions.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"

begin
  
 home= getenv("HOME")   
  diri_obs  =home + "/work/An_En_RA/obs/Ray_windfarm"
     diro      = home+ "/work/An_En_RA/Input/"
     site="Ray_Wind_Farm"
;outfile stuff
        delimiter="  "
        file_out_prefix="AN_EN_RA"
        file_out_postfix=str_sub_str(site, " ", "_")
        file_out=diro+file_out_prefix+"_"+file_out_postfix

; get the data
        nrows= numAsciiRow(file_out)   ; contributed.ncl
        ncols = numAsciiCol(file_out)
        print("nrows: "+nrows)
        print("ncols"+ncols)
	tempo=asciiread(file_out,-1,"float")
	data=  onedtond(tempo(21:), (/nrows,ncols/))  ; MUST know starting index
printVarSummary(data)
R_b_nr_point=data(:,24)
non_missing_idx=ind(.not.ismissing(data(:,25)))
obs_wind_70m=data(:,25)
nwp_wind_80m=data(:,6)
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


 res@lgOrientation          = "horizontal"     ; Default is vertical
  res@pmLegendWidthF         = 0.75             ; Make it wider
  res@pmLegendOrthogonalPosF = -0.1             ; Move it up slightly
  res@lgPerimOn              = False            ; Turn off the perimeter box
  res@xyMarkerColor = "blue"
  res@tiMainString  = "Make your own marker"
  res@xyMarkers     = NhlNewMarker(wks, "^", 19, 0.0, 0.0, 1.3125, 1.5, 0.0)
  plot              = gsn_csm_xy (wks,obs_wind_70m(non_missing_idx),nwp_wind_80m(non_missing_idx),res)
;
delete(res)
delete(colors)
; compute stability distribution 
opt=True
opt@bin_max=0.2
opt@bin_min=-0.2
R_b_pdf = pdfx(R_b_nr_point,13,opt)
percent =R_b_pdf
percent = (/R_b_pdf(0),R_b_pdf(1) ,R_b_pdf(2), R_b_pdf(3),R_b_pdf(4), R_b_pdf(5), R_b_pdf(6),R_b_pdf(7),R_b_pdf(8),R_b_pdf(9),R_b_pdf(10),R_b_pdf(11),R_b_pdf(12)/)
print(percent)
                                 colors   = (/ "red", "green", "orange", "yellow", "brown","magenta","blue","gray" /)
; name    = (/ "Deciduous", "Savanna", "Wetland", "Tundra", "Evergreen", "Desert", "Cropland", "Grassland" /)

; pcRes   = True
 res  = True
if 1.eq.1  then
 res@gsnDraw                = True
 res@gsnFrame               = True
 res@xyLineThicknessF       = 4
 res@xyLineColors           =(/"red"/)
 res@tiXAxisString          = "Bulk Richardson number"
 res@tiYAxisString          = "Frequency of occurrence (%) "
 res@trXMinF                =-0.2
 res@trXMaxF                =0.2
 res@tmXMajorGrid                = True          ; implement x grid 
 res@tmXMajorGridThicknessF      = 1.0           ; 2.0 is default
 res@tmXMajorGridLineDashPattern = 2             ; select short dash lines
 res@tmYMajorGrid                = True          ; implement y grid
 res@tmYMajorGridThicknessF      = 1.0           ; 2.0 is default
 res@tmYMajorGridLineDashPattern = 2             ; select short dash lines
                                                                       
  res@xyMarkLineMode     ="MarkLines"
 res@xyMarkerSizeF      = 0.03
 res@xyMarkerThicknessF = 3.
  res@xyMonoMarkerColor  = True          ; Allow different colors for markers
 res@xyMarkerColors     = colors(6:)
print("in resource loop½")
end if




wks                        = gsn_open_wks("pdf","R_b_pdf_xy")
 plot                       = gsn_csm_xy (wks, R_b_pdf@bin_center, R_b_pdf, res)

end 
