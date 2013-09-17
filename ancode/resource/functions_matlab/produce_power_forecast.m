function [ power_forecast] = produce_power_forecast(dates_analog,Namelist,good_turbine_data)
%PRODUCE_POWER_FORECAST Summary of this function goes here
%   Detailed explanation goes here

switch 1
    
    case Namelist{6}.Analog_to_wind
        power_forecast=get_wind_from_analog(dates_analog,Namelist,good_turbine_data)
        power_forecast=get_air_density_from_analog(dates_analog,Namelist,good_turbine_data)
    case Namelist{6}.Analog_to_power
        
end %switch 


end

