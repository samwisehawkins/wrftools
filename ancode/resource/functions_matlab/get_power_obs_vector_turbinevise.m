function [ power_obs_vector ] = get_power_obs_vector_turbinevise(forecast_vector,in_turbine_data,num_obs_dates,num_obs_nacelle_winds,Namelist)
%GET_POWER_OBS_VECTOR Summary of this function goes here
%   Detailed explanation goes here

%parsing section
switch 1
    case Namelist{6}.Analog_to_turbine_power
        good_turbine_data=in_turbine_data.power_production;
        start_date_num=datenum(forecast_vector.var_data{2,1}(1,:),Namelist{1}.datstr_general_format);%=';
        display(strcat('Forecast starting at:',datestr(start_date_num,Namelist{1}.datstr_general_format)))
        obs_date=start_date_num;

        for i=1:length(Namelist{5}.Analog.lead_times)   
            display(strcat('Forecast for date:',datestr(obs_date,Namelist{1}.datstr_general_format)));
            %[val idx]=min(abs(obs_date-num_obs_dates))
             idx=find(abs(obs_date-num_obs_dates)<1.1574e-005);
                if not(isempty(idx))
                    power_obs_vector.power_obs(i)=good_turbine_data{1,3}(idx(1));
                    power_obs_vector.turbineid(i)=good_turbine_data{1,1}(1);
                    power_obs_vector.mean_nacelle_wspd(i)=good_turbine_data{1,4}(idx(1));
                else
                    power_obs_vector.power_obs(i)=Namelist{1}.missing_value;
                    power_obs_vector.turbineid(i)=good_turbine_data{1,1}(1);
                    power_obs_vector.mean_nacelle_wspd(i)=Namelist{1}.missing_value;
                end %if is empty
                    power_obs_vector.valid_date(i,:)=datestr(obs_date,Namelist{1}.datstr_general_format);
                    obs_date=addtodate(obs_date, Namelist{5}.Analog.lead_delta, 'hour');
                    obs_date=datenum(datestr(obs_date,Namelist{1}.datstr_general_format),Namelist{1}.datstr_general_format);
        end % for
    
    case Namelist{6}.Analog_to_turbine_wind
        good_turbine_data=in_turbine_data.power_production;
        start_date_num=datenum(forecast_vector.var_data{2,1}(1,:),Namelist{1}.datstr_general_format);%=';
      %  display(strcat('Forecast starting at:',datestr(start_date_num,Namelist{1}.datstr_general_format)));
        obs_date=start_date_num;
      
        for i=1:length(Namelist{5}.Analog.lead_times)   
            % find in wind obs days (significant mnore than power obs days )
            idx=find(abs(obs_date-num_obs_nacelle_winds)<1.1574e-005);
            idx_power=find(abs(obs_date-num_obs_dates)<1.1574e-005);
            if not(isempty(idx))
                    if not(isempty(idx_power))
                        power_obs_vector.power_obs(i)=good_turbine_data{1,3}(idx_power(1));
                    else 
                        power_obs_vector.power_obs(i)=Namelist{1}.missing_value;
                     end 
                    power_obs_vector.turbineid(i)=good_turbine_data{1,1}(1);
                    power_obs_vector.mean_nacelle_wspd(i)=in_turbine_data.wind_all{1,4}(idx(1));
                else
                    power_obs_vector.power_obs(i)=Namelist{1}.missing_value;
                    power_obs_vector.turbineid(i)=good_turbine_data{1,1}(1);
                    power_obs_vector.mean_nacelle_wspd(i)=Namelist{1}.missing_value;
                end %if is empty
                    power_obs_vector.valid_date(i,:)=datestr(obs_date,Namelist{1}.datstr_general_format);
                    obs_date=addtodate(obs_date, Namelist{5}.Analog.lead_delta, 'hour');
                    obs_date=datenum(datestr(obs_date,Namelist{1}.datstr_general_format),Namelist{1}.datstr_general_format);
            
            
        end
end





end

