function [ regression_constants ] = get_regression_constants(good_turbine_data,time_serie_nwp_forecast,Namelist)
%UNTITLED3 Summary of this function goes here
%   Detailed explanation goes here
datenum_start=datenum(Namelist{5}.start_analog_search_period,Namelist{1}.datstr_turbine_input_format);
datenum_end=datenum(Namelist{5}.end_second_analog_search_period,Namelist{1}.datstr_turbine_input_format);

    num_dates_nwp_total=datenum(time_serie_nwp_forecast{1,2},Namelist{1}.datstr_general_format);
    whichstats = {'beta' 'r' 'tstat' 'mse' 'dwstat'};
    lead_time_counter=0;
    [m n]=size(good_turbine_data);
    
    for turbine=1:n
        num_dates_obs=datenum(good_turbine_data(1,turbine).power_production{1,2},Namelist{1}.datstr_general_format);
        for i=Namelist{1,5}.Analog.lead_times
            % make sure to only compare in same period as analogs are
            % trained and extract on right lead time
            num_dates_nwp=num_dates_nwp_total(find(datenum(time_serie_nwp_forecast{1,2},Namelist{1}.datstr_general_format)>datenum_start & datenum(time_serie_nwp_forecast{1,2},Namelist{1}.datstr_general_format)<datenum_end & str2num(time_serie_nwp_forecast{1,14})==i));
            nwp_wspd=time_serie_nwp_forecast{1,6}(find(datenum(time_serie_nwp_forecast{1,2},Namelist{1}.datstr_general_format)>datenum_start & datenum(time_serie_nwp_forecast{1,2},Namelist{1}.datstr_general_format)<datenum_end & str2num(time_serie_nwp_forecast{1,14})==i));
            % make sure we are in same training period as analogs 
            % match dates from nwp to obs
            % get the predicar and the predictand
            for j=1:length(num_dates_nwp)
                idx=find(abs(num_dates_nwp(j)-num_dates_obs)<Namelist{1}.minutes_in_fraction_of_a_day);
                if not(isempty(idx))
                    predictor_1(j)=nwp_wspd(j);
                    predictand(j)=good_turbine_data(1,turbine).power_production{1,4}(idx);
                else
                    predictor_1(j)=Namelist{1}.missing_value;
                    predictand(j)=Namelist{1}.missing_value;
                end
            end
            stat(turbine,i)=regstats(predictand,predictor_1,'linear',whichstats); % proved regression coefficients 
            reg_percentiles_on_lead_times{turbine,i} = quantile(stat(1,i).r,[.025 .25 .50 .75 .975]);
            display(['operating on leadtime:',num2str(i),' Turbine:',num2str(turbine)])
            predictor_1_after_correction=(predictor_1*stat(turbine,i).beta(2))+stat(turbine,i).beta(1);        
            idx=find(predictor_1~=Namelist{1}.missing_value);
            plot(predictor_1(idx),'r');hold on; plot(predictand(idx),'b');hold on;plot(predictor_1_after_correction(idx),':black');hold off
            legend({'Raw nwp','Raw nacelle wind','Corrected nwp'});ylabel('Windspeed','fontsize',15);set(gca,'fontsize',15);grid on
            
        end
    end % turbine id
        save_dir=Namelist{4}.reg_stat_dir
        save_file=[Namelist{4}.reg_stat_dir,'\stats']
                    if isdir(save_dir)
                        save(save_file,'stat','reg_percentiles_on_lead_times')
                    else
                        mkdir(save_dir)
                        save(save_file,'stat','reg_percentiles_on_lead_times')
                    end
