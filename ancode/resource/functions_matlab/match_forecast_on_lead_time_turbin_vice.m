function [ dates weights ] = match_forecast_on_lead_time_turbin_vice(Historical_forecast_vector,forecast_vector,Namelist,leadtime,good_turbine_data,num_obs_dates)
%MATCH_FORECAST_ON_LEAD_TIME Summary of this function goes here
%   Detailed explanation goes here

% first compute all distances

distance_on_lead_time=get_distance_on_lead_time(Historical_forecast_vector,forecast_vector,Namelist,leadtime);
% now get the index for the 10 best analogs 
if Namelist{5}.Analog.remove_self_analogs % do not allow that forecast vector is refound as analog
    [dummy_dis dummy_idx]=sort(distance_on_lead_time);
    analog_dis=dummy_dis(2:length(dummy_dis));
    analog_idx=dummy_idx(2:length(dummy_idx));  % remove first entry as this is forecast_vector=analog_vector
else %cheeting
    [analog_dis analog_idx]=sort(distance_on_lead_time);
end
% now get the sorted dates for the
% Namelist{5}.Analog.number_of_analogs_search_for best analogs 1 is the one
% best matching option to make sure good observation exist for the found dates else take new ones 
    dates.dates='01-09-2010 12:00';
    % check what is observed close to anlog dates or power or wind obs
    % exist  for each turbine 
if Namelist{6}.make_sure_obs_exist_for_each_analog_for_each_turbine==1
    %turbine loop
    for i=1:length(good_turbine_data) % number of turbines 
       switch 1
           case Namelist{6}.Analog_to_turbine_power
               num_obs_dates=datenum(good_turbine_data(1,i).power_production{1,2},'dd-mm-yyyy HH:MM:SS');
           case Namelist{6}.Analog_to_turbine_wind
               num_obs_dates=datenum(good_turbine_data(1,i).wind_all{1,2},'dd-mm-yyyy HH:MM:SS');
       end %switch
       done=0;
       date_counter=1;
       dates(i).dates=['01-03-1970 12:00'];% initialize dates value
        dummy=1;
    
     while not(done)& dummy<=length(Historical_forecast_vector.var_data{2,1}(analog_idx,:))
                %find index for analogs in observation
                idx_tmp=find(abs((datenum(Historical_forecast_vector.var_data{2,1}(analog_idx(dummy),:),Namelist{1}.datstr_general_format)-num_obs_dates))<(Namelist{5}.Analog.time_window_minutes*Namelist{1}.minutes_in_fraction_of_a_day));
                datestr(num_obs_dates(idx_tmp),Namelist{1}.datstr_general_format);
                if length(idx_tmp)>1
                    %pick closest
                    [c,indexmin]=min(num_obs_dates(idx_tmp)-datenum(Historical_forecast_vector.var_data{2,1}(analog_idx(dummy),:),Namelist{1}.datstr_general_format));
                   idx=idx_tmp(indexmin); 
                else
                    idx=idx_tmp;
                end 
                % check if good observation exists
                if good_turbine_data(1,i).power_production{1,4}(1)<25 & ~isempty(idx)% make sure wind speed is below cutout tresshold
                    dates(i).turbine_id=good_turbine_data(1,i).power_production{1,1};
                    dates(i).dates(date_counter,:)=Historical_forecast_vector.var_data{2,1}(analog_idx(dummy),:);
                    date_counter=date_counter+1;
                    dummy=dummy+1;
                else
                    dummy=dummy+1;
                end
                  [ m n] =size(dates(i).dates);
                  if m==Namelist{5}.Analog.number_of_analogs_search_for
                      done=1;
                  end
            end
    end % for number of turbines 
else % tjeck for existing observations 
     for i=1:length(good_turbine_data) % number of turbines 
       num_obs_dates=datenum(good_turbine_data(1,i).power_production{1,2},'dd-mm-yyyy HH:MM:SS');
       done=0;
       date_counter=1;
       dates(i).dates=['01-03-1970 12:00'];% initialize dates value
       dummy=1;
       % 2012-0917 dates
       dates(i).dates=Historical_forecast_vector.var_data{2,1}(analog_idx(1:Namelist{5}.Analog.number_of_analogs_search_for),:);
       dates(i).turbine_id=good_turbine_data(1,i).power_production{1,1};
     end % turbine loop obsolute becouse all turbine have the same analog dates when we do not care id obs exist!
    
end
% make sure good observation exist for the found dates else take new ones 

%now get the sorted Weights for the
% Namelist{5}.Analog.number_of_analogs_search_for best analogs 1 is the one
% best matching
% 2 is hard coded becaouse first analog it the forecast itself Change when
% going to reel time 
norm_factor=1./analog_dis(2:Namelist{5}.Analog.number_of_analogs_search_for);
    for i=2:Namelist{5}.Analog.number_of_analogs_search_for
        weights(i)=((1/analog_dis(i)))/sum(norm_factor);
    end
 % check the results 
 analogmtx(1,:)=Historical_forecast_vector.var_data{2,2}(analog_idx(1:Namelist{5}.Analog.number_of_analogs_search_for)); %wspd
 analogmtx(2,:)=Historical_forecast_vector.var_data{2,3}(analog_idx(1:Namelist{5}.Analog.number_of_analogs_search_for)); %wdirection
 analogmtx(3,:)=Historical_forecast_vector.var_data{2,4}(analog_idx(1:Namelist{5}.Analog.number_of_analogs_search_for)); % sea level preasure
 analogmtx(4,:)=Historical_forecast_vector.var_data{2,5}(analog_idx(1:Namelist{5}.Analog.number_of_analogs_search_for)); %Air density
 
 if Namelist{7}.analog_plot
     subplot(4,1,1)
     hist(analogmtx(1,:));legend(strcat('True:',num2str(forecast_vector.var_data{2,2}),' m/s'));grid on;
     subplot(4,1,2)
     hist(analogmtx(2,:));legend(strcat('True:',num2str(forecast_vector.var_data{2,3}),' Degree north'));grid on;
     subplot(4,1,3)
     hist(analogmtx(3,:));legend(strcat('True:',num2str(forecast_vector.var_data{2,4}),' hpa'));grid on;
     subplot(4,1,4)
     hist(analogmtx(4,:));legend(strcat('True:',num2str(forecast_vector.var_data{2,5}),' kg/m3'));grid on;
     filename=strcat(Namelist{1}.plots_data_dir,'Analog_ditribution on lead_',num2str(leadtime),Namelist{5}.Analog.now)
     print('-djpeg',filename)

 end % if 

end

