function [ good_turbine_data time_serie_nwp_forecast num_obs_dates clean_turbine_data] = load_data( Namelist )
%LOAD_DATA Summary of this function goes here
%   Read in the ETA or wrf nwp forecast 
%   Reads in the turbine observbations 

if Namelist{3}.get_data_from_saved_work_spaces
    switch 1
        case strcmp(Namelist{2}.location{1},'sprogoe')& strcmp(Namelist{4}.nwp_model{1},'ETA')
            data_path=[Namelist{1}.workspace_data_dir '\' 'sprogø_long_14']
            load(data_path) % get clean turbine data
           % time consuming task - needed to match obs dates with forecast
        case strcmp(Namelist{2}.location{1},'sprogoe')& strcmp(Namelist{4}.nwp_model{1},'WRF')
            data_path=[Namelist{1}.workspace_data_dir '\','Sprogoe_02']
            load(data_path) % get clean turbine data
            num_obs_dates=999
      end% switch 
else
    switch 1
        case strcmp(Namelist{4}.nwp_model{1},'ETA')
            time_serie_nwp_forecast=get_time_series_ETAforecast(Namelist);
            time_serie_nwp_forecast=up_date_time_serie_nwp_forecast(Namelist,time_serie_nwp_forecast)
            time_serie_nwp_forecast=get_std_on_nwp_variables(time_serie_nwp_forecast);
            
        case strcmp(Namelist{4}.nwp_model{1},'WRF')
            
            if Namelist{1}.use_all_forecast_files
                tempo_1=get_time_series_WRFforecast_2(Namelist);
                Namelist{5}.start_analog_search_period=Namelist{5}.start_second_analog_search_period
                Namelist{5}.end_analog_search_period=Namelist{5}.end_second_analog_search_period
                Namelist{4}.WRF_sst_fields=Namelist{4}.WRF_second_sst_fields
                Namelist{1}.forecast_data_dir=strcat(Namelist{1}.root_dir,'/data/nwp/wrf/Historical_files_',Namelist{4}.WRF_sst_fields)
                tempo_2=get_time_series_WRFforecast_2(Namelist);
                tempo_3=get_time_series_WRFforecast_updates(Namelist);
                for i=1:length(tempo_3)
                    switch 1
                        case not(isempty(tempo_1))&not(isempty(tempo_2))&not(isempty(tempo_3))
                            time_serie_nwp_forecast{1,i}=vertcat(tempo_1{1,i}, tempo_2{1,i}, tempo_2{1,i});
                            time_serie_nwp_forecast{2,i}=tempo_1{2,i}
                        case not(isempty(tempo_2))&not(isempty(tempo_3))
                            time_serie_nwp_forecast{1,i}=vertcat(tempo_2{1,i}, tempo_3{1,i});
                            time_serie_nwp_forecast{2,i}=tempo_2{2,i}
                        case not(isempty(tempo_3))
                            time_serie_nwp_forecast{1,i}=tempo_3{1,i};
                            time_serie_nwp_forecast{2,i}=tempo_3{2,i};
                    end % switch
                end
                time_serie_nwp_forecast=get_diagnostics_on_nwp_variables(time_serie_nwp_forecast,Namelist);
                time_serie_nwp_forecast=get_std_on_nwp_variables(time_serie_nwp_forecast);
                
            else
                time_serie_nwp_forecast=get_time_series_WRFforecast_2(Namelist);
                time_serie_nwp_forecast=get_std_on_nwp_variables(time_serie_nwp_forecast);
                time_serie_nwp_forecast=get_diagnostics_on_nwp_variables(time_serie_nwp_forecast,Namelist);
                
            end
       case strcmp(Namelist{4}.nwp_model{1},'ECMWF')
            time_serie_nwp_forecast=get_time_series_ECMWFforecast(Namelist);
            time_serie_nwp_forecast=get_std_on_nwp_variables(time_serie_nwp_forecast);
            time_serie_nwp_forecast=get_diagnostics_on_nwp_variables(time_serie_nwp_forecast,Namelist);
           
    end %switch
    
    if Namelist{3}.use_new_observations
         turbine_data=get_turbine_data_3(Namelist);
         switch 1
             case Namelist{5}.use_clean_obs_turbine_by_turbine;
                    clean_turbine_data=get_turbine_data_2_cleaned_turbine_vice(Namelist);     
                    good_turbine_data=parse_obs_turbine_by_turbine(Namelist,clean_turbine_data) % to be corrected no working
                    num_obs_dates=999
 
             case Namelist{5}.use_clean_obs_park_level % else get it parkvice 
                    clean_turbine_data=get_turbine_data_2_cleaned(Namelist,turbine_data);       
                    good_turbine_data=get_total_turbine_power_production_2(Namelist,clean_turbine_data)
                     num_obs_dates=datenum(good_turbine_data{1,2},Namelist{1}.datstr_turbine_input_format)
              case Namelist{5}.use_clean_obs~=1; %dont use clean obs
                  good_turbine_data=get_total_turbine_power_production_2(Namelist,turbine_data);
                  num_obs_dates=datenum(good_turbine_data{1,2},Namelist{1}.datstr_turbine_input_format)
             
                 
        end % switch 
         
    else % use old data 
        turbine_data=get_turbine_data_2(Namelist);    
        clean_turbine_data=get_turbine_data_2_cleaned(Namelist,turbine_data);
        if Namelist{5}.use_clean_obs==1;
          good_turbine_data=get_total_turbine_power_production_2(Namelist,clean_turbine_data)
           num_obs_dates=datenum(good_turbine_data{1,2},Namelist{1}.datstr_turbine_input_format)
 
      else
         good_turbine_data=get_total_turbine_power_production_2(Namelist,turbine_data)
          num_obs_dates=datenum(good_turbine_data{1,2},Namelist{1}.datstr_turbine_input_format)
 
        end 
    end
    % load the cleaned data 
    
    
    
    %Time_series_marked=get_time_series_marked(Namelist);
end % if read from work space 
% make sure nwp time series are within the expected range 
[val start_idx]=min(abs(datenum(Namelist{5}.start_training_period,'yyyy-mm-dd HH:MM')-datenum(time_serie_nwp_forecast{1,2},Namelist{1}.datstr_general_format)))
[val end_idx] =min(abs(datenum(Namelist{5}.end_training_period,'yyyy-mm-dd HH:MM')-datenum(time_serie_nwp_forecast{1,2},Namelist{1}.datstr_general_format)))

[m n]=size(time_serie_nwp_forecast)

for i=1:n-1
    if not(isempty(time_serie_nwp_forecast{1,i}))
        time_serie_nwp_forecast{1,i}=time_serie_nwp_forecast{1,i}(start_idx:end_idx,:);
        datenum(time_serie_nwp_forecast{1,1},Namelist{1}.datstr_general_format);
    end 
end
  
% calculates the errors 
end % function 



