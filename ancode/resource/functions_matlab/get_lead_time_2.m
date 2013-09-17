function [ lead_time ] = get_lead_time_2( Namelist,time_serie_nwp_forecast)
%GET_LEAD_TIME Summary of this function goes here
%   Detailed explanation goes here WRF version= init time is the same for 
% here convert valid date to num
n_init=datenum((time_serie_nwp_forecast{1,1}),Namelist{1}.datstr_general_format);
n_valid=datenum((time_serie_nwp_forecast{1,2}),Namelist{1}.datstr_general_format);
n_diff=n_valid-n_init
h_diff=n_diff*24
for i=1:length(n_diff)
lead_time(i)=round(h_diff(i));
end
  lead_time=num2str(lead_time')
end