function [raw_nwp_power local_power] = get_time_serie_power_forecast_regression(data_in,forecast_vector,power_forecast,Namelist,first_time,power_obs_vectorhe,turbine_counter);
%GET_TIME_SERIE_POWER_FORECAST_REGRESSION Summary of this function goes here
%   Detailed explanation goes here
load([Namelist{4}.reg_stat_dir,'\stats']);
[power_curve ] = get_power_curve( Namelist );


% do downscaling 
forecasted_winds=forecast_vector.var_data{2,2};
forecasted_densities=forecast_vector.var_data{2,5};

forecasted_lead_times=str2num(forecast_vector.var_data{2,6});
lead_idx=find(Namelist{1,5}.Analog.lead_times==forecasted_lead_times');
 [m n]=size(stat);
    for lead=1:length(forecasted_lead_times)
        local_winds(lead)=forecasted_winds(lead)*stat(turbine_counter,forecasted_lead_times(lead)).beta(2)+stat(turbine_counter,forecasted_lead_times(lead)).beta(1);
        [min_difference, windspeed_index]   = min(abs(power_curve{1,2} - local_winds(lead)));
        [min_difference, air_density_index] = min(abs(power_curve{1,1} -forecasted_densities(lead) ));
        local_power(lead,1)=power_curve{1,3}{air_density_index}(windspeed_index);
        [min_difference, windspeed_index]   = min(abs(power_curve{1,2} - forecasted_winds(lead)));
        raw_nwp_power(lead,1)=power_curve{1,3}{air_density_index}(windspeed_index);
        clear windspeed_index;
        clear air_density_index;
    end  %i loop
    

   
