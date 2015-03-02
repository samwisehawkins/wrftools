;**********************************************************************
; Template for ncl options. 
; This template is filled in, and written to a the ncl_opt_file  
; file as specified in the main configuration
; it is then 'passed' to ncl via an environment variable NCL_OPT_FILE
;***********************************************************************

ncl_in_file   = "<ncl_in_file>"
ncl_out_dir   = "<ncl_out_dir>"
ncl_out_file  = "<ncl_out_file>"
ncl_out_type  = "<ncl_out_type>"
ncl_loc_file  = "<ncl_loc_file>"



;*********************************************************
; Options below are only used in extract_time_series.ncl
; And controls which variable are extracted, and various
; options controling how they are interpolated
;*********************************************************

;******************************************************
; Time-series options
;******************************************************
    extract_heights = <extract_heights>
    tsopts = True

    ;**************************************************
    ; Horizontal interpolation options
    ; 0: none, use grid cell value from wrf_user_ll_to_ij (not implemented yet!)
    ; 1: inverse distance weighting as implemented by rcm2points(opt=1)
    ; 2: bilinear interpolation as implemented by rcm2points(opt=2)
    ;**************************************************
    tsopts@interp_option = 2

    ;**************************************************
    ; Time units
        tsopts@time_units = 1
    ;                 0 units of "hours since" initial time on the current file (type "double")
    ;                 1 returns units of "hours since 1901-01-01 00:00:00" (type "double")
    ;                 2 returns units of "yyyymmddhhmnss" (type "double")
    ;                 3 returns units of "yyyymmddhh" (type "integer")
    ;**************************************************


    ;**************************************************
    ; Bulk richardson options.
    ; TODO, allow these to be arrays,
    ; so we can do multiple heights
    ; rib_opt=1        ; AMS versions
        tsopts@rib_opt=2     ; Zilintikivich et al
    tsopts@rib_i_lower = 2         ; lower (extract_height) index
    tsopts@rib_i_upper = 4         ; upper (extract_height) index
    ;**************************************************

;******************************************************


;******************************************************
; Variables
;******************************************************

    ;**********************************
    ; 3D variables
    ;**********************************
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


    ;**********************************
    ; 2D (surface or averaged) variables
    ;**********************************
    vars@rib               = True      ;Bulk Richardson number                   - output as RIB
    vars@sst               = True      ;sea-surface temperature                  - output as SST
    vars@tsk               = False     ;skin (surface) temperature               - output as TSK
    vars@t2                = True      ;temperature at 2m                        - output as T2
    vars@td2               = True      ;dewpoint temperature at 2m               - output as TD2
    vars@pblh              = True      ;PBL height                               - output as PBLH
    vars@psfc              = True      ;pressure at the surface                  - output as PSFC
    vars@swdown            = True      ;downward short wave flux at ground surface -- output as SWDOWN
    vars@cldfraavg         = True      ;cloud fraction column average              -- output as CLDFRAAVG
    vars@cldframax         = True      ;cloud fraction column maximun              -- output as CLDFRAMAX
    vars@rain              = True      ;total grid scale precipitation           - output as RAIN
    vars@slp               = True      ;sea-level pressure- using WRF-NCL        - not yet implemented
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

