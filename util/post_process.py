import os
import subprocess
import sys

for f in sys.argv[1:]:
    path, name  = os.path.split(f)
    dest = "/longbackup/slha/forecasting/domains/baseline_europe/highres/processed"
        
    newname = dest+'/'+name
    #cmd = "ncks -4 -l 9 -v U,V,W,PH,PHB,T,MU,MUB,P,ALT,PB,P_HYD,Q2,T2,TH2,PSFC,U10,V10,ITIMESTEP,QVAPOR,QCLOUD,QRAIN,GRDFLX,SSTSK,TKE_PBL,EL_PBL,SINALPHA,COSALPHA,HGT,TSK,P_TOP,T00,P00,TLP,RAINC,RAINSH,RAINNC,SNOWNC,GRAUPELNC,HAILNC,CLDFRA,SWDOWN,GLW,SWNORM,XLAT,XLONG,XLAT_U,XLONG_U,XLAT_V,XLONG_V,TMN,XLAND,UST,PBLH,HFX,QFX,LH,SNOWC,SR,LANDMASK,SST -d bottom_top,0,4 -d bottom_top,7,7 -d bottom_top,14,14 %s %s" % (f, newname)
    #cmd = "ncks -4 -l 9 -v U,V,W,PH,PHB,T,MU,MUB,P,PB,P_HYD,Q2,T2,TH2,PSFC,U10,V10,ITIMESTEP,QVAPOR,QCLOUD,QRAIN,GRDFLX,SSTSK,TKE_PBL,EL_PBL,SINALPHA,COSALPHA,HGT,TSK,P_TOP,T00,P00,TLP,RAINC,RAINSH,RAINNC,SNOWNC,GRAUPELNC,HAILNC,CLDFRA,SWDOWN,GLW,SWNORM,XLAT,XLONG,XLAT_U,XLONG_U,XLAT_V,XLONG_V,TMN,XLAND,UST,PBLH,HFX,QFX,LH,SNOWC,SR,LANDMASK,SST -d bottom_top,0,4 -d bottom_top,7,7 -d bottom_top,14,14 %s %s" % (f, newname)

    #varlist = "LU_INDEX,ZNU,ZNW,ZS,DZS,VAR_SSO,LAP_HGT,HFX_FORCE,LH_FORCE,TSK_FORCE,HFX_FORCE_TEND,LH_FORCE_TEND,TSK_FORCE_TEND,NEST_POS,FNM,FNP,RDNW,RDN,DNW,DN,CFN,CFN1,RDX,RDY,RESM,CF1,CF2,CF3,SHDMAX,SHDMIN,SNOALB,TSLB,SMOIS,SH2O,SMCREL,SEAICE,XICEM,SFROFF,UDROFF,IVGTYP,ISLTYP,VEGFRA,ACGRDFLX,ACSNOM,SNOW,SNOWH,CANWAT,LAI,VAR,MAPFAC_M,MAPFAC_U,MAPFAC_V,MAPFAC_MX,MAPFAC_MY,MAPFAC_UX,MAPFAC_UY,MAPFAC_VX,MF_VX_INV,MAPFAC_VY,F,E,TISO,MAX_MSTFX,MAX_MSTFY,REFL_10CM,OLR,ALBEDO,CLAT,ALBBCK,EMISS,NOAHRES,FLX4,FVB,FBUR,FGSN,ACHFX,ACLHF,SAVE_TOPO_FROM_REAL,SEED1,SEED2".split(",")
    varlist = "LU_INDEX,ZNU,ZNW,ZS,DZS,NEST_POS,FNM,FNP,RDNW,RDN,DNW,DN,CFN,CFN1,RDX,RDY,RESM,CF1,CF2,CF3,TSLB,SEAICE,IVGTYP,ISLTYP,VEGFRA,ACGRDFLX,LAI,MAPFAC_M,F,E,TISO,MAX_MSTFX,MAX_MSTFY,OLR,ALBEDO,ALBBCK,ACHFX,ACLHF,SAVE_TOPO_FROM_REAL,SEED1,SEED2,XLAT_U,XLONG_U,XLAT_V,XLONG_V"
    levels = "-d bottom_top,0,25 -d bottom_top_stag,0,26"
    cmd = "ncks -4 -l 9 -O -x -v %s %s %s %s" % (varlist, levels, f, newname)
    print cmd
    subprocess.call(cmd, shell=True)


    
    #upper_name = dest+'/'+name.replace('wrfout', 'wrfout_upr')
    #varlist = "PHB,PH,P_HYD,T,U,V,W"
    #levels = "-d bottom_top,14,14 -d bottom_top_stag,14,15"
    #cmd = "ncks -4 -l 9 -O -v %s %s %s %s" % (varlist, levels, f, upper_name)
    #print cmd
    #subprocess.call(cmd, shell=True)
    #or not os.path.exists(upper_name):
    
    if not os.path.exists(newname):
        print 'something gone wrong'
        continue
    else:
        os.remove(f)
        # rename the lower-level files back to original name
        #os.rename(newname, f)
