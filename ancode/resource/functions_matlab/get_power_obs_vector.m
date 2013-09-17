function [ power_obs_vector ] = get_power_obs_vector(forecast_vector,in_turbine_data,num_obs_dates,Namelist)
%GET_POWER_OBS_VECTOR Summary of this function goes here
%   Detailed explanation goes here

%parsing section
if Namelist{6}.Analog_to_turbine_power
    good_turbine_data=in_turbine_data.power_production
else
    good_turbine_data=in_turbine_data
end


start_date_num=datenum(forecast_vector.var_data{2,1}(1,:),Namelist{1}.datstr_general_format);%=';
%display(strcat('Forecast starting at:',datestr(start_date_num,Namelist{1}.datstr_general_format)));
obs_date=start_date_num;
for i=1:length(Namelist{5}.Analog.lead_times)   
    %[val idx]=min(abs(obs_date-num_obs_dates))
     idx=find(abs(obs_date-num_obs_dates)<1.1574e-005);
        if not(isempty(idx))
            power_obs_vector.power_obs(i)=good_turbine_data{1,3}(idx(1));
            power_obs_vector.nr_turbines_producing(i)=good_turbine_data{1,1}(idx(1));
            power_obs_vector.mean_nacelle_wspd(i)=good_turbine_data{1,4}(idx(1));
            if Namelist{7}.adjust_for_non_producing_turbines
            % remember to correct for 0 observation turbines as this causes nans     
               power_obs_vector.corrected_obs_vector.power_obs(i)=(Namelist{1}.number_of_turbines_in_park/power_obs_vector.nr_turbines_producing(i))*good_turbine_data{1,3}(idx(1));
            end
            
            
        else
            power_obs_vector.power_obs(i)=Namelist{1}.missing_value;
            power_obs_vector.nr_turbines_producing(i)=Namelist{1}.missing_value;
            power_obs_vector.mean_nacelle_wspd(i)=Namelist{1}.missing_value;
            power_obs_vector.corrected_obs_vector.power_obs(i)=Namelist{1}.missing_value;
        end %if is empty
            power_obs_vector.valid_date(i,:)=datestr(obs_date,Namelist{1}.datstr_general_format);
            obs_date=addtodate(obs_date, Namelist{5}.Analog.lead_delta, 'hour');
            obs_date=datenum(datestr(obs_date,Namelist{1}.datstr_general_format),Namelist{1}.datstr_general_format);
end % for

end

