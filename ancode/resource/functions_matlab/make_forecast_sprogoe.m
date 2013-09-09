function [ new_forecast ] = make_forecast_sprogoe(lates_init_time,Namelist,first_time)
%if updates are made save info on update times  
 time_input=[Namelist{1}.run_time_in_put,'\times.mat'];
 verif=[Namelist{1}.run_time_in_put,'\verif.mat'];
 run_time=[Namelist{1}.run_time_in_put,'\init_files.mat'];
 forecast=[Namelist{1}.run_time_in_put,'\power_forecast.mat'];
 mkdir(Namelist{1}.run_time_in_put);
 plot_test=[Namelist{1}.run_time_in_put,'\plot_testing'];
 num_obs_dates=999;
 load(time_input);
%attemp to get the newest nwp data
                 
         switch 1 
             case lates_init_time_runs_exist(Namelist,lates_init_time) 
                    load(verif)
                    load(run_time)
                    Namelist{5}.Analog.now=lates_init_time 
                    Namelist{5}.Analog.lead_times=set_analog_leadtimes(Namelist,1) 
                    
                    [m n]=size(good_turbine_data); 
                    [time_serie_nwp_forecast updated]=update_timeseries(time_serie_nwp_forecast,lates_init_time,Namelist)
                    forecast_vector=get_forecast_vector(Namelist,time_serie_nwp_forecast);
                    dates_analog=get_dates_analog(Namelist,forecast_vector,time_serie_nwp_forecast,good_turbine_data,num_obs_dates);
                    
                    for i=1:n
                       power_obs_vector(i)=get_power_obs_vector_turbinevise(forecast_vector,good_turbine_data(1,i),datenum(good_turbine_data(1,i).power_production{1,2},'dd-mm-yyyy HH:MM:SS'),datenum(good_turbine_data(1,i).power_production{1,2},'dd-mm-yyyy HH:MM:SS'),Namelist);
                       power_forecast{i}=get_power_from_analog(dates_analog,Namelist,good_turbine_data,num_obs_dates,datenum(good_turbine_data(1,i).wind_all{1,2},'dd-mm-yyyy HH:MM:SS'),i,forecast_vector,time_serie_nwp_forecast);
                       turbine_time_series(i).data=get_time_serie_power_forecast(turbine_time_series(i).data,forecast_vector,power_forecast{i},Namelist,first_time,power_obs_vector(1,i),i);
                    end
                    
                      new_forecast=1
                      last_updated=lates_init_time;save(time_input,'last_updated')
                      save(verif,'turbine_time_series') 
                      save(run_time,'good_turbine_data','time_serie_nwp_forecast','clean_turbine_data','turbine_time_series') 
                      save(forecast,'power_forecast')                  
             
             case (lates_init_time_runs_exist(Namelist,datestr(addtodate(datenum(lates_init_time),-12,'hour'),'yyyy-mm-dd HH:MM'))) ...
             & (addtodate(datenum(lates_init_time),-12,'hour')>datenum(last_updated))
                  load(verif)
                  load(run_time)
                  Namelist{5}.Analog.lead_times=set_analog_leadtimes(Namelist,2) 
                  Namelist{5}.Analog.now=datestr(addtodate(datenum(lates_init_time),-12,'hour'),'yyyy-mm-dd HH:MM')
                 [m n]=size(good_turbine_data);
                % update with new forecast time series 
                    [time_serie_nwp_forecast updated]=update_timeseries(time_serie_nwp_forecast,...
                    datestr(addtodate(datenum(lates_init_time),-12,'hour'),'yyyy-mm-dd HH:MM'),Namelist)
                    forecast_vector=get_forecast_vector(Namelist,time_serie_nwp_forecast);
                    dates_analog=get_dates_analog(Namelist,forecast_vector,time_serie_nwp_forecast,good_turbine_data,num_obs_dates);                 
                  %Turbine loop
                      for i=1:n
                           power_obs_vector(i)=get_power_obs_vector_turbinevise(forecast_vector,good_turbine_data(1,i),datenum(good_turbine_data(1,i).power_production{1,2},'dd-mm-yyyy HH:MM:SS'),datenum(good_turbine_data(1,i).power_production{1,2},'dd-mm-yyyy HH:MM:SS'),Namelist);
                           power_forecast{i}=get_power_from_analog(dates_analog,Namelist,good_turbine_data,num_obs_dates,datenum(good_turbine_data(1,i).wind_all{1,2},'dd-mm-yyyy HH:MM:SS'),i,forecast_vector,time_serie_nwp_forecast);
                           turbine_time_series(i).data=get_time_serie_power_forecast(turbine_time_series(i).data,forecast_vector,power_forecast{i},Namelist,first_time,power_obs_vector(1,i),i);
                      end
                      first_time=0
                      new_forecast=1;
                      %save section 
                      last_updated=datestr(addtodate(datenum(lates_init_time),-12,'hour'),'yyyy-mm-dd HH:MM');save(time_input, 'last_updated')
                      save(verif,'turbine_time_series') 
                      save(run_time,'good_turbine_data','time_serie_nwp_forecast','clean_turbine_data','turbine_time_series') 
                      save(forecast,'power_forecast') 
                      %sendmail(jesn38@gmail.com,'Forecast updated','test')
             case (datenum(lates_init_time)==datenum(last_updated))... % newest init file used and forecast updated
                  | (addtodate(datenum(lates_init_time),-12,'hour')==datenum(last_updated))
                 disp('Forecast upto date')
                 new_forecast=0
             case 1
                 disp(['forecast more than ',sprintf('%03d',24*(datenum(lates_init_time)-datenum(last_updated))),' hours old'])
         end
         
    testing=0
    if new_forecast
        if testing
            load(plot_test) 
        end 
     %upload stuff Now uploading for Lem Kær 
     
     %Availabilty_vector=[1 1 1 1 1 1 1]
     %[ counts out_filename ] = parse_to_power_hub(Namelist,Availabilty_vector)
     %[succes]=upload_forecast( Namelist,out_filename)
    % plot section 
     plot_succes=plot_power_forecast_turbine_vice_2(turbine_time_series,power_obs_vector,Namelist,last_updated);
                
     
 end 
 

