function [time_serie_power_forecast ] = get_time_serie_power_forecast(time_serie_power_forecast,forecast_vector,power_forecast,Namelist,first_time,power_obs_vector,turbine_counter)
%GET_TIME_SERIE_POWER_FORECAST Summary of this function goes here
%   Detailed explanation goes here
if first_time
        time_serie_power_forecast{1,1}='Valid time';
        time_serie_power_forecast{1,2}='deterministic power forecast';
        time_serie_power_forecast{1,3}='10 % percentile';
        time_serie_power_forecast{1,4}='20 % percentile';
        time_serie_power_forecast{1,5}='30 % percentile';
        time_serie_power_forecast{1,6}='40 % percentile';
        time_serie_power_forecast{1,7}='50 % percentile';
        time_serie_power_forecast{1,8}='60 % percentile';
        time_serie_power_forecast{1,9}='70 % percentile';
        time_serie_power_forecast{1,10}='80 % percentile';
        time_serie_power_forecast{1,11}='90 % percentile';
        time_serie_power_forecast{1,12}='STD ensemble(Spread)';
        time_serie_power_forecast{1,13}='Ensemble mean';
        time_serie_power_forecast{1,14}='Weighted distribution';
        time_serie_power_forecast{1,15}='Total Power Production Observed';
        time_serie_power_forecast{1,16}='NR producing Turbine';
        time_serie_power_forecast{1,17}='Analog_weights';
        time_serie_power_forecast{1,18}='Power distribution';
        time_serie_power_forecast{1,19}='Regresion power forecast';
        time_serie_power_forecast{1,20}='raw nwp power forecast';
        time_serie_power_forecast{1,21}='observed nacelle wind';
        time_serie_power_forecast{1,22}='deterministic forecasted wind';
        time_serie_power_forecast{1,23}='Forecasted wind distribution';
        
        
        

        
end      % first time
        for i=1:length(Namelist{5}.Analog.lead_times)
            tempo{2,1}=forecast_vector.var_data{2,1};
            tempo{2,2}(i,1)=power_forecast(1,i).deterministic_power_forecast;
            tempo{2,3}(i,1)=power_forecast(1,i).percentiles_from_power_distribution(1);
            tempo{2,4}(i,1)=power_forecast(1,i).percentiles_from_power_distribution(2);
            tempo{2,5}(i,1)=power_forecast(1,i).percentiles_from_power_distribution(3);
            tempo{2,6}(i,1)=power_forecast(1,i).percentiles_from_power_distribution(4);
            tempo{2,7}(i,1)=power_forecast(1,i).percentiles_from_power_distribution(5);
            tempo{2,8}(i,1)=power_forecast(1,i).percentiles_from_power_distribution(6);
            tempo{2,9}(i,1)=power_forecast(1,i).percentiles_from_power_distribution(7);
            tempo{2,10}(i,1)=power_forecast(1,i).percentiles_from_power_distribution(8);
            tempo{2,11}(i,1)=power_forecast(1,i).percentiles_from_power_distribution(9);
            tempo{2,12}(i,1)=std(power_forecast(1,i).power_distribution);
            tempo{2,13}(i,1)=mean(power_forecast(1,i).power_distribution);
            tempo{2,14}(i,:)=power_forecast(1,i).weighted_power_distribution;
            %tempo{2,17}(i,:)=power_forecast(1,i).Analog_weights;
            tempo{2,18}(i,:)=power_forecast(1,i).power_distribution;
            if Namelist{10}.do_regression
           [tempo{2,20} tempo{2,19}] = get_time_serie_power_forecast_regression(time_serie_power_forecast,forecast_vector,power_forecast,Namelist,first_time,power_obs_vector,turbine_counter);
            end
            tempo{2,21}(i,1)=power_obs_vector.mean_nacelle_wspd(i);
            tempo{2,23}(i,:)=power_forecast(1,i).wind.distribution;
            tempo{2,22}(i,1)=mean(power_forecast(1,i).wind.distribution);
            
            
        end
        
        if Namelist{10}.nwp_to_power_forecast_method==2
         tempo{2,15}=power_obs_vector.power_obs';
         tempo{2,16}=1;
        else
         tempo{2,15}=power_obs_vector.corrected_obs_vector.power_obs';
         tempo{2,16}=power_obs_vector.nr_turbines_producing';
        end
        % wait untill all done
         %Now RMSE on Ensemble mean - observation 
         %tempo{2,13}=RMSEdecomp(tempo{2,15},tempo{2,13}) 
         %(((tempo{2,13}-tempo{2,15}).^2)./length(tempo{2,14})).^0.5;
         
% merge with existing time serie 
        if first_time
             time_serie_power_forecast{2,1}=tempo{2,1};
             time_serie_power_forecast{2,2}=tempo{2,2};
             time_serie_power_forecast{2,3}=tempo{2,3};
             time_serie_power_forecast{2,4}=tempo{2,4};
             time_serie_power_forecast{2,5}=tempo{2,5};
             time_serie_power_forecast{2,6}=tempo{2,6};
             time_serie_power_forecast{2,7}=tempo{2,7};
             time_serie_power_forecast{2,8}=tempo{2,8};
             time_serie_power_forecast{2,9}=tempo{2,9};
             time_serie_power_forecast{2,10}=tempo{2,10};
             time_serie_power_forecast{2,11}=tempo{2,11};
             time_serie_power_forecast{2,12}=tempo{2,12};
             time_serie_power_forecast{2,13}=tempo{2,13};
             time_serie_power_forecast{2,14}=tempo{2,14};
             time_serie_power_forecast{2,15}=tempo{2,15};
             time_serie_power_forecast{2,16}=tempo{2,16};
             %time_serie_power_forecast{2,17}=tempo{2,17};
             time_serie_power_forecast{2,18}=tempo{2,18};
             if Namelist{10}.do_regression
                [tempo{2,20} tempo{2,19}] = get_time_serie_power_forecast_regression(time_serie_power_forecast,forecast_vector,power_forecast,Namelist,first_time,power_obs_vector,turbine_counter);
                time_serie_power_forecast{2,19}=double(tempo{2,19});
                time_serie_power_forecast{2,20}=double(tempo{2,20});
             end
             time_serie_power_forecast{2,21}=tempo{2,21};
             time_serie_power_forecast{2,22}=tempo{2,22};
             time_serie_power_forecast{2,23}=tempo{2,23};
           
             
             
             
        else
             time_serie_power_forecast{2,1}=vertcat(time_serie_power_forecast{2,1},tempo{2,1});
             time_serie_power_forecast{2,2}=vertcat(time_serie_power_forecast{2,2},tempo{2,2});
             time_serie_power_forecast{2,3}=vertcat(time_serie_power_forecast{2,3},tempo{2,3});
             time_serie_power_forecast{2,4}=vertcat(time_serie_power_forecast{2,4},tempo{2,4});
             time_serie_power_forecast{2,5}=vertcat(time_serie_power_forecast{2,5},tempo{2,5});
             time_serie_power_forecast{2,6}=vertcat(time_serie_power_forecast{2,6},tempo{2,6});
             time_serie_power_forecast{2,7}=vertcat(time_serie_power_forecast{2,7},tempo{2,7});
             time_serie_power_forecast{2,8}=vertcat(time_serie_power_forecast{2,8},tempo{2,8});
             time_serie_power_forecast{2,9}=vertcat(time_serie_power_forecast{2,9},tempo{2,9});
             time_serie_power_forecast{2,10}=vertcat(time_serie_power_forecast{2,10},tempo{2,10});
             time_serie_power_forecast{2,11}=vertcat(time_serie_power_forecast{2,11},tempo{2,11});
             time_serie_power_forecast{2,12}=vertcat(time_serie_power_forecast{2,12},tempo{2,12});
             time_serie_power_forecast{2,13}=vertcat(time_serie_power_forecast{2,13},tempo{2,13});
             time_serie_power_forecast{2,14}=vertcat(time_serie_power_forecast{2,14},tempo{2,14});
             time_serie_power_forecast{2,15}=vertcat(time_serie_power_forecast{2,15},tempo{2,15});
             time_serie_power_forecast{2,16}=vertcat(time_serie_power_forecast{2,16},tempo{2,16});
             %time_serie_power_forecast{2,17}=vertcat(time_serie_power_forecast{2,17},tempo{2,17});
             time_serie_power_forecast{2,18}=vertcat(time_serie_power_forecast{2,18},tempo{2,18});
             if Namelist{10}.do_regression
                 time_serie_power_forecast{2,19}=vertcat(time_serie_power_forecast{2,19},double(tempo{2,19}));
                 time_serie_power_forecast{2,20}=vertcat(time_serie_power_forecast{2,20},double(tempo{2,20}));
             end
             time_serie_power_forecast{2,21}=vertcat(time_serie_power_forecast{2,21},tempo{2,21});
             time_serie_power_forecast{2,22}=vertcat(time_serie_power_forecast{2,22},tempo{2,22});
             time_serie_power_forecast{2,23}=vertcat(time_serie_power_forecast{2,23},tempo{2,23});
            
        end
end

