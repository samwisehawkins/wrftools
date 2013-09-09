function [power_distribution weighted_power_distribution percentiles_from_power_distribution deterministic_power good_weights] = get_power_distribution_from_turbine(turbine_dates,turbine_power,turbine_analog_dates,lead,Namelist,weights,num_obs_dates)
%GET_WEIGHTED_POWER_DISTRIBUTION Summary of this function goes here
%   Detailed explanation goes here
% first tjeck if all turbines are producing as surposed to
%get idx for observation 
      
      num_obs_dates=datenum(turbine_dates,'dd-mm-yyyy HH:MM:SS');
      num_analog_dates=datenum(turbine_analog_dates.dates,'dd-mm-yyyy HH:MM');
          
        for j=1:Namelist{5}.Analog.number_of_analogs_search_for % loop trough all analogs for the given turbine 
                idx_tmp=find(abs(num_analog_dates(j)-num_obs_dates)<(Namelist{5}.Analog.time_window_minutes*Namelist{1}.minutes_in_fraction_of_a_day));
                if length(idx_tmp)>1
                    %pick closest
                    [c,indexmin]=min(num_obs_dates(idx_tmp)-num_analog_dates(j));
                   idx(j)=idx_tmp(indexmin); 
                else
                    idx(j)=idx_tmp;
                end
            end % for analogs 

   deterministic_power=mean(turbine_power(idx));
   percentiles_from_power_distribution=prctile(turbine_power(idx),Namelist{7}.power_production_percentiles);
   power_distribution=turbine_power(idx);
   weighted_power_distribution=Namelist{1}.missing_value;
        good_weights=Namelist{1}.missing_value;
end %switch
        


