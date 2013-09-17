function [wind_distribution weighted_wind_distribution percentiles_from_wind_distribution deterministic_wind good_weights] = get_wind_distribution_from_turbine(turbine_dates,turbine_wind,turbine_analog_dates,lead,Namelist,weights,num_obs_dates)
%GET_WEIGHTED_POWER_DISTRIBUTION Summary of this function goes here
% first tjeck if all turbines are producing as surposed to
%get idx for observation 
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
   deterministic_wind=mean(turbine_wind(idx));
   percentiles_from_wind_distribution=prctile(turbine_wind(idx),Namelist{7}.power_production_percentiles);
   wind_distribution=turbine_wind(idx);
   weighted_wind_distribution=Namelist{1}.missing_value;
   good_weights=Namelist{1}.missing_value;
end %switch
        


