function [ hit_rate false_alarm_rate  ] = do_roc_diagram( Namelist,analogs )
%DO_ROC_DIAGRAM Summary of this function goes here
%   Detailed explanation goes here

close all
    exp_name='Turbine_by_turbine_winter_training_12_months_2011'
    file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\ETA\out\experiments\',exp_name]
    filename=strcat('\turbine_time_series_for_nr_analogs_',num2str(analogs))
    load([file_path,filename])
    leadtime_vector=get_leadtime_vector(turbine_time_series,Namelist)'
    [ analogs_lead_times ] = get_analog_lead_times( Namelist );
    nr_analogs=num2str(analogs)
    for j=analogs_lead_times
        obs=[];model=[];model_ensembles=[];model_ensembles_variance=[];
        [m n]=size(turbine_time_series)
        for i=1:n
            % concanate loop
            good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value & leadtime_vector==j);
            obs=vertcat(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw,obs);
            model=vertcat(turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw,model);
            model_ensembles=vertcat(turbine_time_series(1,i).data{2,18}(good_idx{i},:)/Namelist{10}.rated_capasity_kw,model_ensembles);
            
        end
        
        % verification of ETA prob model agains observation 
        % normalize all power data 
             a=0 ; %event forecast and occur
             b=0 ; % event forecasted but dit not occur
             c=0;  %event not forecast but did occur
             d=0;  % event not forecast and did not occur all is good very good
             first_time=1
             counter=0
             event_tresshold=0.20 % turbine producing less than 20%
             treshold_counter=0
             
        % Verification loop on lead time      
        nr_obs=length(obs)
        fixed_tresshold_values=[0:0.10:1]
        max_treshold_counter=length(fixed_tresshold_values)
        for fixed_tresshold=fixed_tresshold_values
            treshold_counter=treshold_counter+1
            p_a(j,treshold_counter)=0;p_b(j,treshold_counter)=0;p_c(j,treshold_counter)=0;p_d(j,treshold_counter)=0;
            
            for i=1:nr_obs 
              %desision_treshold_power=prctile(model_ensembles(i,:),(100-(fixed_tresshold)*100));
              desision_treshold_power=prctile(model_ensembles(i,:),((fixed_tresshold)*100));
              switch 1
                     case desision_treshold_power<event_tresshold % forecast mindre end event_tresshold
                         % update right number according to observation
                         if obs(i)<event_tresshold;
                                    % Event forecasted and took place 
                             p_a(j,treshold_counter)=p_a(j,treshold_counter)+1;
                         else       % Event forecasted but did not take place 
                             p_b(j,treshold_counter)=p_b(j,treshold_counter)+1;
                         end
                     case desision_treshold_power>event_tresshold % event not forecasted 
                         % update right number according to observation
                         if obs(i)<event_tresshold;
                             % event not forecasted but took place 
                             p_c(j,treshold_counter)=p_c(j,treshold_counter)+1;
                         else % event not forecasted and did not take place 
                             p_d(j,treshold_counter)=p_d(j,treshold_counter)+1;
                         end
                   end
             end % obs loops 
        end % tresshold loop
        
           hit_rate=p_a./(p_a+p_c);hit_rate(find(isnan(hit_rate)))=0;
           false_alarm_rate=p_b./(p_b+p_d);false_alarm_rate(find(isnan(false_alarm_rate)))=0;
           hit_rate=cat(2, ones(j,1),hit_rate)
           false_alarm_rate=cat(2,ones(j,1),false_alarm_rate)
           
            % do roc diagram
            figure
            plot(false_alarm_rate(j,:),hit_rate(j,:));grid on
            title(['lead-',num2str(j)]);xlabel('False alarm rates');ylabel('Hit rates')
            save_dir=[Namelist{1}.stat_plot_dir,'\prob-plots']
            plot_filename=['\roc_diagram_',nr_analogs,'_analogs_wrf_shear_turbine-lead-',num2str(j),'H']
                    if isdir(save_dir)
                       saveas(gcf,[save_dir plot_filename] ,'fig')
                       saveas(gcf,[save_dir plot_filename] ,'jpeg')

                    else
                        mkdir(save_dir)
                        saveas(gcf,[save_dir plot_filename] ,'fig')
                        saveas(gcf,[save_dir plot_filename] ,'jpeg')

                    end
            
    end % analogs leadtime
    
end

