function [ Namelist ] = set_Namelist_forecast_Lem_kaer( )
%SET_NAMELIST Summary of this function goes here
%   Detailed explanation goes here
%SET_NAMELIST Summary of this function goes here
%   Detailed explanation goes here


%SET_NAMELIST Summary of this function goes here
%   Detailed explanation goes here
%SET_NAMELIST Summary of this function goes here
%   Detailed explanation goes here

Namelist{1}.experiment='Lem_kaer_analog_to_wind_2011-12-01 11_00_2012-09-15 00_00_domaine_3'
Namelist{1}.root_dir='/Users/jesper_nissen/Documents/MATLAB/work/AnEn'
Namelist{1}.run_time_in_put=[Namelist{1}.root_dir,'/data/Real_time_forecasting/LemKaer/workspace']
Namelist{1}.forecast_initial_time=[0  12 ]
Namelist{1}.look_back_cycles=[5]
Namelist{1}.turbine_data_file(1,:)=[ Namelist{1}.root_dir,'/Data/Observations/Sprogoe_offshore_windfarm_new_fileds_1.csv']
Namelist{1}.turbine_by_turbine_data_file=[ Namelist{1}.root_dir,'/data/workspace/turbine_vise_obs/'];
Namelist{1}.ecmwf_eps_dir_in='/Users/jesper_nissen/Documents/MATLAB/work/AnEn/data/nwp/ECMWF/EPS/time_series'
Namelist{1}.sekund_in_fraction_of_a_day=(1/(24*60*60))
Namelist{1}.minutes_in_fraction_of_a_day=(1/(24*60))
Namelist{1}.missing_value=-999
Namelist{1}.number_of_turbines_in_park=4
%Namelist{1}.power_curve_file='C:/Users/jnini/Matlab/work/AnEn/data/Powe_curves/V90_3_0_MW_VCS.txt'V112?3_0_MW_noise_mode_0
Namelist{1}.power_curve_file='/Users/jesper_nissen/Documents/MATLAB/work/AnEn/data/Powe_curves/V112_3_0_MW_noise_mode_0.txt'

Namelist{2}.forecast_in_dir=Namelist{1}.run_time_in_put

Namelist{1}.datstr_turbine_input_format='yyyy-mm-dd HH:MM'
Namelist{1}.datstr_som_label_format='dd-mm-yyyy_HH:MM:SS'
Namelist{1}.datstr_som_label_format='yyyy-mm-dd_HH:MM:SS'
Namelist{1}.datstr_general_format='dd-mm-yyyy HH:MM'
Namelist{1}.workspace_data_dir_in= [ Namelist{1}.root_dir,'/data/workspace']
Namelist{1}.workspace_clean_obs_dir= '/Users/jesper_nissen/Documents/MATLAB/work/data_extract_ms_sql/Data/power_obs/'
Namelist{1}.html_plots='//dkrdshomedir01/initial_j$/jnini/Store/Documents/Projects/Accuaracy_in_power_forecasting/html/power_forecast'
Namelist{1}.html_department_plots='Y:/Group_Technology_RD/_Confidential/Global Research/Energy Systems/Department/Projects/01 Running projects/TE-21312 Short term power forecasting/html/power_forecast'
Namelist{1}.html_department_2_plots='C:/Users/jnini/Dropbox/Public/html/power_forecast'

Namelist{4}.WRF_forecast_fields{1}='Init_time'
    Namelist{4}.WRF_forecast_fields{2}='Valid_time'
    Namelist{4}.WRF_forecast_fields{3}='TMP 2m' 
    Namelist{4}.WRF_forecast_fields{4}='TMP 0_30mb'
    Namelist{4}.WRF_forecast_fields{5}='RH 2m'
    Namelist{4}.WRF_forecast_fields{6}='wspd 10m'
    Namelist{4}.WRF_forecast_fields{7}='wdir 10m'
    Namelist{4}.WRF_forecast_fields{8}='wspd 0_30mb'
    Namelist{4}.WRF_forecast_fields{9}='wdir 0_30mb'
    Namelist{4}.WRF_forecast_fields{10}='MSP'
    Namelist{4}.WRF_forecast_fields{11}='FRICV'
    Namelist{4}.WRF_forecast_fields{12}='rho 10m' 
    Namelist{4}.WRF_forecast_fields{13}='rho 0_30mb'
    Namelist{4}.WRF_sst_fields='41M/'
    Namelist{4}.WRF_second_sst_fields='41MH/'
    Namelist{2}.location{1}='LemKaer'
    switch 1
        case strcmp(Namelist{2}.location{1},'sprogoe')
            Namelist{1}.turbine_data_file(1,:)=[ Namelist{1}.root_dir,...
            '/Data/Observations/Sprogoe_offshore_windfarm_new_fileds_1.csv']
        
    end 
    Namelist{3}.get_data_from_saved_work_spaces=0
    Namelist{3}.use_new_observations=1
    Namelist{4}.ETA_forecast_fields{1}='Init_time'
    Namelist{4}.ETA_forecast_fields{2}='Valid_time'
    Namelist{4}.ETA_forecast_fields{3}='TMP 2m' 
    Namelist{4}.ETA_forecast_fields{4}='TMP 0_30mb'
    Namelist{4}.ETA_forecast_fields{5}='RH 2m'
    Namelist{4}.ETA_forecast_fields{6}='wspd 10m'
    Namelist{4}.ETA_forecast_fields{7}='wdir 10m'
    Namelist{4}.ETA_forecast_fields{8}='wspd 0_30mb'
    Namelist{4}.ETA_forecast_fields{9}='wdir 0_30mb'
    Namelist{4}.ETA_forecast_fields{10}='MSP'
    Namelist{4}.ETA_forecast_fields{11}='FRICV'
    Namelist{4}.ETA_forecast_fields{12}='rho 10m' 
    Namelist{4}.ETA_forecast_fields{13}='rho 0_30mb'
    Namelist{4}.ETA_forecast_fields{14}='Lead time h'


Namelist{4}.nwp_model{1}='WRF'
Namelist{4}.nwp_model_domain=3

switch 1
    case strcmp(Namelist{4}.nwp_model{1},'WRF')
        Namelist{1}.forecast_data_dir=strcat([ Namelist{1}.root_dir,'/data/nwp/wrf/Historical_files_',Namelist{4}.WRF_sst_fields])
        Namelist{1}.forcast_data_timerseries=strcat([ Namelist{1}.root_dir,'/data/nwp/wrf/forecast_data_time_series'])
        Namelist{1}.forcast_data_2d_fileds=strcat([ Namelist{1}.root_dir,'/data/nwp/wrf/forecast_data_2_d_data/'])
        Namelist{1}.datstr_WRF_input_format='yyyy-mm-dd_HH:MM'
        Namelist{1}.use_all_forecast_files=1
        Namelist{1}.workspace_data_dir_in=[ Namelist{1}.root_dir,'/data/workspace','/',Namelist{4}.nwp_model{1},'/Input']
        Namelist{1}.workspace_data_dir_out=[ Namelist{1}.root_dir,'/data/workspace','/',Namelist{4}.nwp_model{1},'/Out']
        %Namelist{2}.forecast_out_dir=['C:/Users/jnini/MATLAB/work/Forecast_system/data/forecast_out_dir/',Namelist{4}.nwp_model{1},'/',Namelist{2}.location{1}]
        Namelist{2}.forecast_out_dir=[Namelist{1}.root_dir,'/data/Real_time_forecasting/LemKaer/',Namelist{4}.nwp_model{1}]
        Namelist{1}.plots_data_dir= [ Namelist{1}.root_dir,'/plots/','/',Namelist{4}.nwp_model{1}]
        Namelist{1}.plots_forecast_dir= [ Namelist{1}.root_dir,'/plots/day_ahead_forecast/',Namelist{4}.nwp_model{1}]
        Namelist{1}.plots_forecast_dir_turbine_vice=[Namelist{1}.root_dir,'/Real_time_forecasting/plots/day_ahead_forecast/',Namelist{4}.nwp_model{1},'/',Namelist{1}.experiment]
        
        Namelist{1}.diagnostics_shear_heights_levels=[3 6]
        Namelist{1}.diagnostics_Bulk_ricardson_heights_levels=[0 6] % 0=surface value
        

    case strcmp(Namelist{4}.nwp_model{1},'ETA')
        Namelist{1}.workspace_data_dir_in=[ Namelist{1}.root_dir,'/data/workspace','/',Namelist{4}.nwp_model{1},'/Input']
        Namelist{1}.workspace_data_dir_out=[ Namelist{1}.root_dir,'/data/workspace','/',Namelist{4}.nwp_model{1},'/Out']
        Namelist{1}.forcast_data_timerseries=strcat([ Namelist{1}.root_dir,'/data/nwp/Eta/Historical_files_',Namelist{4}.WRF_sst_fields])
        Namelist{1}.forcast_data_2d_fileds=strcat([ Namelist{1}.root_dir,'/data/nwp/Eta/forecast_data_2_d_data/'])
        Namelist{1}.datstr_ETA_input_format='yyyy-mm-dd HH:MM:SS'

        Namelist{1}.forecast_data_file_sprogoe=[ Namelist{1}.root_dir,'/Data/nwp/Eta/hist.forecast_ETA_2009-01_2011-12.csv']
        Namelist{1}.forecast_data_file_sprogoe_update=[ Namelist{1}.root_dir,'/Data/nwp/Eta/hist.forecast_ETA_2011_2012_03.csv']
        Namelist{1}.plots_data_dir= [ Namelist{1}.root_dir,'/plots/','/',Namelist{4}.nwp_model{1}]
        Namelist{1}.plots_forecast_dir= [ Namelist{1}.root_dir,'/plots/day_ahead_forecast/',Namelist{4}.nwp_model{1}]
        Namelist{1}.plots_forecast_dir_turbine_vice=[ Namelist{1}.root_dir,'/plots/day_ahead_forecast/',Namelist{4}.nwp_model{1},'/',Namelist{1}.experiment]

end

Namelist{5}.use_clean_obs=1;
Namelist{5}.use_clean_obs_turbine_by_turbine=1;
Namelist{5}.use_clean_obs_park_level=1; % note that it either turbine vice or parkvice 

%Analog specifics 
switch 1
            case Namelist{4}.nwp_model_domain==3
                Namelist{5}.Analog.lead_times=[24:1:47] % rember lead 1=0 13=12
                Namelist{5}.Analog.lead_delta=Namelist{5}.Analog.lead_times(2)-Namelist{5}.Analog.lead_times(1)
                Namelist{4}.reg_stat_dir=[ Namelist{1}.root_dir,'/data/workspace','/regstats','/model_',Namelist{4}.nwp_model{1},'/domaine_',num2str(Namelist{4}.nwp_model_domain)];
                
            case Namelist{4}.nwp_model_domain==2
                Namelist{5}.Analog.lead_times=[12:3:36] % rember lead 1=0 13=12
                Namelist{5}.Analog.lead_delta=Namelist{5}.Analog.lead_times(2)-Namelist{5}.Analog.lead_times(1)
                Namelist{1}.stat_dir=[ Namelist{1}.root_dir,'/']
                Namelist{4}.reg_stat_dir=[ Namelist{1}.root_dir,'/data/workspace','/regstats','/model_',Namelist{4}.nwp_model{1},'/domaine_',num2str(Namelist{4}.nwp_model_domain)];

           case Namelist{4}.nwp_model_domain==1
                Namelist{5}.Analog.lead_times=[12:3:36] % rember lead 1=0 13=12
                Namelist{5}.Analog.lead_delta=Namelist{5}.Analog.lead_times(2)-Namelist{5}.Analog.lead_times(1)
                Namelist{4}.reg_stat_dir=[ Namelist{1}.root_dir,'/data/workspace','/regstats','/model_',Namelist{4}.nwp_model{1},'/domaine_',num2str(Namelist{4}.nwp_model_domain)];

        end
Namelist{5}.Analog.number_of_analogs_search_for=10;
Namelist{5}.Analog.time_window_minutes=11; % allows to pick observation that varified within this amounts of minutres from the forecst
%Namelist{5}.Analog.now='2010-08-31 12:00'
%Namelist{5}.Analog.now='2010-11-01 12:00'
%Namelist{5}.Analog.now='2010-11-29 12:00'

%Namelist{5}.Analog.state_vector_idx=[2 6 7 10 13 14 42]
%Namelist{5}.Analog.state_vector_idx=[2 6 7 10 13 14]
%sprogø Namelist{5}.Analog.state_vector_idx=[2    6      7     10  13    14   15      19      23     27    31     35     39]
%sprogø Namelist{5}.Analog.weights_state_vector_idx=[0.1 0.124 0.1  0.1 0.1  0.1 0.132 0.1642 0.159 0.146 0.126  0.009  0.05]
%Namelist{5}.Analog.weights_state_vector_idx=[0.1 1 0.1 0.1 1 1 1 1 1 1 1 1 1 1  ]
%LemKær 
Namelist{5}.Analog.state_vector_idx=[2    6      7     10  13    14   15      19      23     27    31  ]
%Lem Kær 
Namelist{5}.Analog.weights_state_vector_idx=[0.1 0.124 0.1  0.1 0.1  0.1 0.132 0.1642 0.159 0.146 0.126 ]

Namelist{5}.Analog.remove_self_analogs=0

Namelist{5}.Analog.state_vector_range{1}=[]
Namelist{5}.Analog.state_vector_range{2}=[]
Namelist{5}.Analog.state_vector_range{3}=[] 
Namelist{5}.Analog.state_vector_range{4}=[]
Namelist{5}.Analog.state_vector_range{5}=[]
Namelist{5}.Analog.state_vector_range{6}=[3] % meter/second
Namelist{5}.Analog.state_vector_range{7}=[10] % degrees north
Namelist{5}.Analog.state_vector_range{8}=[]
Namelist{5}.Analog.state_vector_range{9}=[]
Namelist{5}.Analog.state_vector_range{10}=[10] %Hpa 
Namelist{5}.Analog.state_vector_range{11}=[]
Namelist{5}.Analog.state_vector_range{12}=[]
Namelist{5}.Analog.state_vector_range{13}=[0.01] % kg/m3


Namelist{5}.start_forecast_period= '2012-02-23 00:00'
Namelist{5}.Analog.now=Namelist{5}.start_forecast_period
Namelist{5}.end_forecast_period= '2012-04-15 00:00'
%Namelist{5}.start_analog_search_period= '2010-10-31 12:00' % should be the same as obs start 
Namelist{5}.start_analog_search_period= '2011-09-01 11:00' % should be the same as obs start 
Namelist{5}.currant_analog_period=Namelist{5}.start_analog_search_period 
Namelist{5}.end_analog_search_period= '2011-12-24 11:00'
Namelist{5}.start_second_analog_search_period= '2011-07-24 12:00'
Namelist{5}.end_second_analog_search_period= '2012-09-15 12:00'
Namelist{5}.start_training_period='2011-12-01 11:00'
Namelist{5}.end_training_period='2012-09-15 00:00'

Namelist{6}.make_sure_obs_exist_for_each_analog_for_each_turbine=1





Namelist{6}.Analog_to_wind=0
Namelist{6}.Analog_to_power=0
Namelist{6}.Analog_to_turbine_power=0
Namelist{6}.Analog_to_turbine_wind=1

% plot section 
Namelist{7}.analog_plot=0
Namelist{7}.bands_percentile_lower=[5] % 30 %
Namelist{7}.bands_percentile_upper=[9] % 70 %
Namelist{7}.fontsize=[30] % 70 %
Namelist{7}.fontsize_sub_plot=22
Namelist{5}.number_ci_plots=2

Namelist{5}.markers(1)='+'	;
Namelist{5}.markers(2)='o'	;
Namelist{5}.markers(3)='*'	;
Namelist{5}.markers(4)='x'	;
Namelist{5}.markers(5)='s'	;
Namelist{5}.markers(6)='d'	;
Namelist{5}.markers(7)='p'	;

Namelist{5}.color{1}='MidnightBlue'	; %white
Namelist{5}.color{2}='DarkGray'
Namelist{5}.color{3}='DarkRed'	;
Namelist{5}.color{4}='DarkOrange'	;
Namelist{5}.color{5}='DarkGoldenrod'	;
Namelist{5}.color{6}='DarkTurquoise'
Namelist{5}.color{7}='Azure'	; %white
Namelist{5}.color{8}='b'
Namelist{5}.color{9}='r'
Namelist{5}.color{10}='k'
Namelist{5}.color{11}='g'

Namelist{5}.linespec{1}='-'
Namelist{5}.linespec{2}='--'
Namelist{5}.linespec{3}=':'
Namelist{5}.linespec{4}='-.'


Namelist{7}.power_production_percentiles=[10:10:90];


Namelist{10}.nwp_to_power_forecast_method=2; %1 = parkvice 2= turbine by turbine
Namelist{10}.do_regression=0
Namelist{10}.name_plate_capasity_kw=21000;
Namelist{10}.rated_capasity_kw=3075;
Namelist{10}.normalize_errors=1;
Namelist{10}.nwp_to_power_forecast_method=2; %1 = parkvice 2= turbine by turbine
Namelist{10}.bin_idx=0.2
Namelist{10}.w2p_use_mean=1
Namelist{10}.air_density_index=5
% wind to power selections (Function:get_power_from_wind_forecast)
Namelist{11}.Benchmarking_add_eps=1
Namelist{10}.w2p_use_som=0
Namelist{10}.w2p_use_analog=0
% impirical power curve
Namelist{12}.use_nr_closest_power_observations=5




end






