function [time_serie_winds ] = get_time_serie_wind(time_serie_winds,forecast_vector,Namelist,first_time,wind_obs,winds,weights)
%GET_TIME_SERIE_POWER_FORECAST Summary of this function goes here
%   Detailed explanation goes here
if first_time
        time_serie_winds{1,1}='Valid time';
        time_serie_winds{1,2}='deterministic wind forecast';
        time_serie_winds{1,3}='10 % percentile';
        time_serie_winds{1,4}='20 % percentile';
        time_serie_winds{1,5}='30 % percentile';
        time_serie_winds{1,6}='40 % percentile';
        time_serie_winds{1,7}='50 % percentile';
        time_serie_winds{1,8}='60 % percentile';
        time_serie_winds{1,9}='70 % percentile';
        time_serie_winds{1,10}='80 % percentile';
        time_serie_winds{1,11}='90 % percentile';
        time_serie_winds{1,12}='STD ensemble(Spread)';
        time_serie_winds{1,13}='Ensemble mean';
        time_serie_winds{1,14}='Weighted distribution';
        time_serie_winds{1,15}='Total Power Production Observed';
        time_serie_winds{1,16}='NR producing Turbine';
        time_serie_winds{1,17}='Analog_weights';
        time_serie_winds{1,18}='Power distribution';
        time_serie_winds{1,19}='Regresion power forecast';
        time_serie_winds{1,20}='raw nwp wind';
        time_serie_winds{1,21}='observed wind';
        time_serie_winds{1,22}='deterministic forecasted wind';
        time_serie_winds{1,23}='Forecasted wind distribution';
        
        
        

        
end      % first time
        for i=1:length(Namelist{5}.Analog.lead_times)
            non_missing_idx=find(not(winds==-999.99));
            tempo{2,1}=forecast_vector.var_data{2,1};
            tempo{2,2}(i,1)=mean(winds(non_missing_idx));
            tempo{2,3}(i,1)=prctile(winds(non_missing_idx),10);
            tempo{2,4}(i,1)=prctile(winds(non_missing_idx),20);
            tempo{2,5}(i,1)=prctile(winds(non_missing_idx),30);
            tempo{2,6}(i,1)=prctile(winds(non_missing_idx),40);
            tempo{2,7}(i,1)=prctile(winds(non_missing_idx),50);
            tempo{2,8}(i,1)=prctile(winds(non_missing_idx),60);
            tempo{2,9}(i,1)=prctile(winds(non_missing_idx),70);
            tempo{2,10}(i,1)=prctile(winds(non_missing_idx),80);
            tempo{2,11}(i,1)=prctile(winds(non_missing_idx),90);
            tempo{2,12}(i,1)=std(winds(non_missing_idx));
            tempo{2,13}(i,1)=mean(winds(non_missing_idx));
            tempo{2,18}(i,:)=winds(); % saving all includning missing values 
        
            if Namelist{10}.do_regression
           [tempo{2,20} tempo{2,19}] = get_time_serie_power_forecast_regression(time_serie_winds,forecast_vector,power_forecast,Namelist,first_time,power_obs_vector,turbine_counter);
            else
              tempo{2,20}=forecast_vector.var_data{4,4};  
            end
            if not(isempty(wind_obs))
                tempo{2,21}(i,1)=wind_obs(1);
            else
                tempo{2,21}(i,1)=Namelist{1}.missing_value;
            end
            
            
        end
  
         
% merge with existing time serie 
        if first_time
             time_serie_winds{2,1}=tempo{2,1};
             time_serie_winds{2,2}=tempo{2,2};
             time_serie_winds{2,3}=tempo{2,3};
             time_serie_winds{2,4}=tempo{2,4};
             time_serie_winds{2,5}=tempo{2,5};
             time_serie_winds{2,6}=tempo{2,6};
             time_serie_winds{2,7}=tempo{2,7};
             time_serie_winds{2,8}=tempo{2,8};
             time_serie_winds{2,9}=tempo{2,9};
             time_serie_winds{2,10}=tempo{2,10};
             time_serie_winds{2,11}=tempo{2,11};
             time_serie_winds{2,12}=tempo{2,12};
             time_serie_winds{2,13}=tempo{2,13};
             time_serie_winds{2,14}=tempo{2,14};
             time_serie_winds{2,15}=tempo{2,15};
             time_serie_winds{2,16}=tempo{2,16};
             %time_serie_power_forecast{2,17}=tempo{2,17};
             time_serie_winds{2,18}=tempo{2,18};
             if Namelist{10}.do_regression
                [tempo{2,20} tempo{2,19}] = get_time_serie_power_forecast_regression(time_serie_winds,forecast_vector,power_forecast,Namelist,first_time,power_obs_vector,turbine_counter);
                time_serie_winds{2,19}=double(tempo{2,19});
                time_serie_winds{2,20}=double(tempo{2,20});
             else
                 time_serie_winds{2,20}=double(tempo{2,20});
             end
                time_serie_winds{2,21}=tempo{2,21};
           
             
             
             
        else
             time_serie_winds{2,1}=vertcat(time_serie_winds{2,1},tempo{2,1});
             time_serie_winds{2,2}=vertcat(time_serie_winds{2,2},tempo{2,2});
             time_serie_winds{2,3}=vertcat(time_serie_winds{2,3},tempo{2,3});
             time_serie_winds{2,4}=vertcat(time_serie_winds{2,4},tempo{2,4});
             time_serie_winds{2,5}=vertcat(time_serie_winds{2,5},tempo{2,5});
             time_serie_winds{2,6}=vertcat(time_serie_winds{2,6},tempo{2,6});
             time_serie_winds{2,7}=vertcat(time_serie_winds{2,7},tempo{2,7});
             time_serie_winds{2,8}=vertcat(time_serie_winds{2,8},tempo{2,8});
             time_serie_winds{2,9}=vertcat(time_serie_winds{2,9},tempo{2,9});
             time_serie_winds{2,10}=vertcat(time_serie_winds{2,10},tempo{2,10});
             time_serie_winds{2,11}=vertcat(time_serie_winds{2,11},tempo{2,11});
             time_serie_winds{2,12}=vertcat(time_serie_winds{2,12},tempo{2,12});
             time_serie_winds{2,13}=vertcat(time_serie_winds{2,13},tempo{2,13});
             time_serie_winds{2,14}=vertcat(time_serie_winds{2,14},tempo{2,14});
             time_serie_winds{2,15}=vertcat(time_serie_winds{2,15},tempo{2,15});
             time_serie_winds{2,16}=vertcat(time_serie_winds{2,16},tempo{2,16});
             %time_serie_power_forecast{2,17}=vertcat(time_serie_power_forecast{2,17},tempo{2,17});
             time_serie_winds{2,18}=vertcat(time_serie_winds{2,18},tempo{2,18});
             if Namelist{10}.do_regression
                 time_serie_winds{2,19}=vertcat(time_serie_winds{2,19},double(tempo{2,19}));
                 time_serie_winds{2,20}=vertcat(time_serie_winds{2,20},double(tempo{2,20}));
             else
                 time_serie_winds{2,20}=vertcat(time_serie_winds{2,20},double(tempo{2,20}));
             end
             time_serie_winds{2,21}=vertcat(time_serie_winds{2,21},tempo{2,21});
            
            
        end
end

