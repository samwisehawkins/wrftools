function [ clean_obs ] = get_turbine_data_2_cleaned_turbine_vice(Namelist);
%GET_TURBINE_DATA_2_CLEANED Summary of this function goes here
%   Detailed explanation goes here

%load([Namelist{1}.workspace_clean_obs_dir,'clean_power_obs_ref_2_turbinevise'])
%load([Namelist{1}.workspace_clean_obs_dir,'clean_power_obs_ref_2_all'])
switch 1
    case strcmp(Namelist{2}.location{1},'sprogoe')
        load([Namelist{1}.workspace_clean_obs_dir,'Sprogoe_power_wind_obs']);
        for i=1:7 % number of turbines
            clean_obs(i)=clean_power_obs_turbinvise{1,i}
        end 
    case strcmp(Namelist{2}.location{1},'LemKaer')
        load([Namelist{1}.workspace_clean_obs_dir,'LemKaer_power_wind_obs']);
        for i=1:4 % number of turbines
            clean_obs(i)=clean_power_obs_turbinvise{1,i}
        end 
end %switch
        
