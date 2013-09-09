function [power_distribution weighted_power_distribution deterministic_power percentiles_from_power_distribution ] = get_power_from_wind_forecast( forecast_vector,time_serie_nwp_forecast,wind_forecast, Namelist,good_turbine_data, lead_time )
%GET_POWER_FROM_WIND_FORECAST Summary of this function goes here called
%from 
% this is the empuirical power curve conversion 
%   Detailed explanation goes here
bin_size_m_s=Namelist{10}.bin_idx;
all_num_valid_dates=datenum(time_serie_nwp_forecast{1,2},'dd-mm-yyyy HH:MM'); % to be moved out of function 

for i=1:length(wind_forecast.wind_distribution)% each nacelle wind speed 
    % get the bin for the predicted nacelle wind 
    done=0;
    while not(done)
        bin_idx=find(good_turbine_data{1,4}<(wind_forecast.wind_distribution(i)+bin_size_m_s) & good_turbine_data{1,4}>(wind_forecast.wind_distribution(i)-bin_size_m_s));
        bin_dates=good_turbine_data{1,2}(bin_idx,:);
        bin_power=good_turbine_data{1,3}(bin_idx);
        num_valid_dates=all_num_valid_dates(find(str2num(time_serie_nwp_forecast{1,14})==lead_time));
        if not(isempty((bin_idx)));
            done=1;
        else
            bin_size_m_s=bin_size_m_s+Namelist{10}.bin_idx*0.005;
            if bin_size_m_s>0.15
                [power_curve ] = get_power_curve( Namelist );
                bin_power=get_power_from_power_curve(Namelist,power_curve,wind_forecast.wind_distribution(i));
                done=1;
            end 
        end 
    end %while
    dummy=0;
    
    switch 1
        case Namelist{10}.w2p_use_mean
            power_distribution(i)=mean(bin_power);
            clear bin_power            
        case Namelist{10}.w2p_use_som
        
        case Namelist{10}.w2p_use_analog
            for j=1:length(bin_idx)%loop trough all obs dates
                tempo=find(abs(num_valid_dates-datenum(bin_dates(j,:),'dd-mm-yyyy HH:MM:SS'))<(11*Namelist{1}.minutes_in_fraction_of_a_day));
                 if not(isempty(tempo))
                     dummy=dummy+1
                      match_idx(dummy)=tempo
                    % now if match exist 
                    %if current forecast vector is sufficiently equal to past forecast if so use verfering obs if not use mean for power 
                 end %if 
            end
    end % switch 
            
     
end %for nacelle winds in forecast vector 

% Endresult 
   deterministic_power=median(power_distribution);
   weighted_power_distribution= 10; %norm_weights.*corrected_observed_power;
   percentiles_from_power_distribution= prctile(power_distribution,Namelist{7}.power_production_percentiles);
   
end

