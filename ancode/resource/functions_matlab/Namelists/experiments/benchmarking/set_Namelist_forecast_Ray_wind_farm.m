function [ Namelist ] = set_Namelist_forecast_Lem_kaer( )
%SET_NAMELIST Summary of this function goes here
%   Detailed explanation goes here
%SET_NAMELIST Summary of this function goes here
%   Detailed explanation goes here



Namelist{1}.experiment='Ray_wind_farm_RA'
Namelist{1}.root_dir='/home/jepn/work/An_En_RA'
% directory stuff
    %Namelist{1}.obs_dir='/Volumes/WRF_DART/Resource_assesment_work/An_EN_output/'
    Namelist{1}.obs_dir=[Namelist{1}.root_dir,'/Input/']
    Namelist{1}.workspace_data_dir_out=strcat(Namelist{1}.root_dir,'/workspaces')
% filename stuff
Namelist{1}.obs_filename='AN_EN_RA_Ray_Wind_Farm'
%formats
Namelist{1}.datstr_turbine_input_format='yyyymmddhh'
Namelist{1,1}.datstr_general_format='yyyymmddhh'
Namelist{1}.missing_value=-999
% nwp stuff
Namelist{4}.nwp_model{1}='WRF-Ris�'

%analogs stuff
Namelist{5}.Analog.number_of_analogs_search_for=3;
Namelist{5}.Analog.time_window_minutes=11; % allows to pick observation that varified within this amounts of minutres from the forecst
Namelist{5}.Analog.state_vector_idx=[3  4  5  6  7  8  9  10  11 14  20  25]
Namelist{5}.Analog.lead_times=[0]

%Ray wind farm 
Namelist{5}.Analog.weights_state_vector_idx=[1  1  1  1  1  1  1  .1  .1  .1 1 1]
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

                                  
Namelist{5}.start_forecast_period= '2008110100'
Namelist{5}.Analog.now=Namelist{5}.start_forecast_period
Namelist{5}.end_forecast_period= '2009110900'
%Namelist{5}.start_analog_search_period= '2010-10-31 12:00' % should be the same as obs start 
Namelist{5}.start_analog_search_period= '2006010100' % should be the same as obs start 
Namelist{5}.currant_analog_period=Namelist{5}.start_analog_search_period 
Namelist{5}.end_analog_search_period= '2006120100'
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

%Namelist{10}.nwp_to_power_forecast_method=2; %1 = parkvice 2= turbine by turbine
Namelist{10}.do_regression=0
Namelist{10}.name_plate_capasity_kw=21000;
Namelist{10}.rated_capasity_kw=3075;
Namelist{10}.normalize_errors=1;
Namelist{10}.nwp_to_power_forecast_method=0;%0 resource assesment %1 = parkvice 2= turbine by turbine
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






