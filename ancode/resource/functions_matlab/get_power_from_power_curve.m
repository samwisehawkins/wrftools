function [ power ] = get_power_from_power_curve(Namelist,power_curve,wspd)
%UNTITLED Summary of this function goes here
%   Detailed explanation goes here
        [min_difference, windspeed_index]   = min(abs(power_curve{1,2} - wspd));
        [air_density_index]=[Namelist{10}.air_density_index];
        power=double(power_curve{1,3}{air_density_index}(windspeed_index));
 end

