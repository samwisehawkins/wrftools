function [ succes ] = do_dispersion_diagram_concanated_turbines( Namelist )
%DO_ACCURACY_NWP_ANALYSIS Summary of this function goes here
%   Detailed explanation goes here
close all
    exp_name='Turbine_by_turbine_winter_training_12_months_2011'
    file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\ETA\out\experiments\',exp_name]
    load([file_path,'\turbine_time_series_for_nr_analogs_20'])
    leadtime_vector=get_leadtime_vector(turbine_time_series,Namelist)'
    [ analogs_lead_times ] = get_analog_lead_times( Namelist );

    for j=analogs_lead_times
        obs=[];model=[];model_ensembles=[];model_ensembles_variance=[];
        [m n]=size(turbine_time_series)
        for i=1:n
            % concanate loop
            good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value & leadtime_vector==j);
            obs=vertcat(turbine_time_series(1,i).data{2,15}(good_idx{i}),obs);
            model=vertcat(turbine_time_series(1,i).data{2,2}(good_idx{i}),model);
            model_ensembles=vertcat(turbine_time_series(1,i).data{2,18}(good_idx{i},:),model_ensembles);
            model_ensembles_variance=vertcat(var(turbine_time_series(1,i).data{2,18}(good_idx{i},:)'/Namelist{10}.rated_capasity_kw)',model_ensembles_variance);
        end
        if not(isempty(obs))
                if Namelist{10}.normalize_errors
                    [ETA_rmse_20(j) ETA_bias_20(j) ETA_crmse_20(j)] = RMSEdecomp_all(obs/Namelist{10}.rated_capasity_kw, model/Namelist{10}.rated_capasity_kw);
                    ETA_spread_20(j)=sqrt(mean(model_ensembles_variance))
                   
                else
                    [ETA_rmse_20(j) ETA_bias_20(j) ETA_crmse_20(j)] = RMSEdecomp_all(obs, model);
                   
                end
        else %isempty
                    ETA_rmse_20(j) =mean(ETA_rmse_20(12:j-1));
                    ETA_spread_20(j)=Namelist{1}.missing_value
                   
                   
       end
 end
    
    clear turbine_time_series;clear obs;clear model
    exp_name_wrf='Turbine_by_turbine_winter_1_mslp_wspd_wdir_rho_shear_domaine_3'
    file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
    load([file_path,'\turbine_time_series_for_nr_analogs_20']);Namelist{4}.nwp_model_domain=3;Namelist{4}.nwp_model{1}='WRF'
    leadtime_vector=get_leadtime_vector(turbine_time_series,Namelist)'
    [ analogs_lead_times_d3 ] = get_analog_lead_times( Namelist );
    
    for j=analogs_lead_times
        obs=[];model=[];model_ensembles=[];model_ensembles_variance=[];
        
    % gets the index where obervation are not missing for each turbine 
    [m n]=size(turbine_time_series)    
        for i=1:n
             % concanate loop
            good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value & leadtime_vector==j);
            obs=vertcat(turbine_time_series(1,i).data{2,15}(good_idx{i}),obs);
            model=vertcat(turbine_time_series(1,i).data{2,2}(good_idx{i}),model);
            model_ensembles=vertcat(turbine_time_series(1,i).data{2,18}(good_idx{i},:),model_ensembles);
            model_ensembles_variance=vertcat(var(turbine_time_series(1,i).data{2,18}(good_idx{i},:)'/Namelist{10}.rated_capasity_kw)',model_ensembles_variance);
        end
           if not(isempty(good_idx{i}))
            if Namelist{10}.normalize_errors
                [WRF_d3_rmse_20(j) WRF_d3_bias_20(j) WRF_d3_crmse_20(j)] = RMSEdecomp_all(obs/Namelist{10}.rated_capasity_kw, model/Namelist{10}.rated_capasity_kw);
                WRF_d3_spread_20(j)=sqrt(mean(model_ensembles_variance))
            else
                [WRF_d3_rmse_20(j) WRF_d3_bias_20(j) WRF_d3_crmse_20(j)] = RMSEdecomp_all(obs, model);
                
            end
           else % is empty 
                WRF_d3_rmse_20(j)=mean(WRF_d3_rmse_20(12:j-1)) 
                WRF_d3_spread_20(j)=Namelist{1}.missing_value
           end % is empty    
        
    end % lead time

    exp_name_wrf='Turbine_by_turbine_winter_1_mslp_wspd_wdir_rho_shear_domaine_2'
    file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
    load([file_path,'\turbine_time_series_for_nr_analogs_20'])
    Namelist{4}.nwp_model_domain=2
    leadtime_vector=get_leadtime_vector(turbine_time_series,Namelist)'
    [ analogs_lead_times_d2 ] = get_analog_lead_times( Namelist );
    obs=[];model=[]

    % gets the index where obervation are not missing for each turbine 
    for j=analogs_lead_times_d2
          obs=[];model=[];model_ensembles=[];model_ensembles_variance=[];

    % gets the index where obervation are not missing for each turbine 
    [m n]=size(turbine_time_series)    
        for i=1:n
            good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value & leadtime_vector==j);
            obs=vertcat(turbine_time_series(1,i).data{2,15}(good_idx{i}),obs);
            model=vertcat(turbine_time_series(1,i).data{2,2}(good_idx{i}),model);
            model_ensembles=vertcat(turbine_time_series(1,i).data{2,18}(good_idx{i},:),model_ensembles);
            model_ensembles_variance=vertcat(var(turbine_time_series(1,i).data{2,18}(good_idx{i},:)'/Namelist{10}.rated_capasity_kw)',model_ensembles_variance);
        end % turbine id 
           if not(isempty(obs))
            if Namelist{10}.normalize_errors
                [WRF_d2_rmse_20(j) WRF_d2_bias_20(j) WRF_d2_crmse_20(j)] = RMSEdecomp_all(obs/Namelist{10}.rated_capasity_kw, model/Namelist{10}.rated_capasity_kw);
                WRF_d2_spread_20(j)=sqrt(mean(model_ensembles_variance))
            else
                [WRF_d2_rmse_20(j) WRF_d2_bias_20(j) WRF_d2_crmse_20(j)] = RMSEdecomp_all(obs, model);
                
            end
           else % isempty(obs)
                WRF_d2_rmse_20(j)=mean(WRF_d2_rmse_20(find(WRF_d2_rmse_20~=0)))                
                WRF_d2_spread_20(j)=Namelist{1}.missing_value
           end
    end % for lead times 

    exp_name_wrf='Turbine_by_turbine_winter_1_mslp_wspd_wdir_rho_shear_domaine_1'
    file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
    load([file_path,'\turbine_time_series_for_nr_analogs_20']);Namelist{4}.nwp_model_domain=1
    leadtime_vector=get_leadtime_vector(turbine_time_series,Namelist)'
    [ analogs_lead_times_d1 ] = get_analog_lead_times( Namelist );
    
    % gets the index where obervation are not missing for each turbine 
    [m n]=size(turbine_time_series)    

    for j=analogs_lead_times_d1
        obs=[];model=[];model_ensembles=[];model_ensembles_variance=[];
        % gets the index where obervation are not missing for each turbine 
    [m n]=size(turbine_time_series)    
        for i=1:n
          good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value & leadtime_vector==j)
          obs=vertcat(turbine_time_series(1,i).data{2,15}(good_idx{i}),obs);
          model=vertcat(turbine_time_series(1,i).data{2,2}(good_idx{i}),model);
          model_ensembles=vertcat(turbine_time_series(1,i).data{2,18}(good_idx{i},:),model_ensembles);
          model_ensembles_variance=vertcat(var(turbine_time_series(1,i).data{2,18}(good_idx{i},:)'/Namelist{10}.rated_capasity_kw)',model_ensembles_variance);
          
        end
           if not(isempty(obs))
            if Namelist{10}.normalize_errors
               [WRF_d1_rmse_20(j) WRF_d1_bias_20(j) WRF_d1_crmse_20(j)] = RMSEdecomp_all(obs/Namelist{10}.rated_capasity_kw, model/Namelist{10}.rated_capasity_kw);
               WRF_d1_spread_20(j)=sqrt(mean(model_ensembles_variance));
            else
                [WRF_d1_rmse_20(j) WRF_d1_bias_20(j) WRF_d1_crmse_20(j)] = RMSEdecomp_all(obs, model);
               
            end
           else
                WRF_d1_rmse_20(j)=mean(WRF_d1_rmse_20(find(WRF_d1_rmse_20~=0))) 
                WRF_d1_spread_20(j)=Namelist{1}.missing_value
               
           end % isempty
        for dummy=1:length(analogs_lead_times_d1)
             lead_time_match_idx(dummy)=find(analogs_lead_times_d1(dummy)==analogs_lead_times_d3)        
        end
    end
    
    mtx_rmse(:,1)=ETA_rmse_20(:,analogs_lead_times_d3(lead_time_match_idx));mtx_rmse(:,:,2)=WRF_d3_rmse_20(:,analogs_lead_times_d3(lead_time_match_idx));mtx_rmse(:,:,3)=WRF_d2_rmse_20(:,analogs_lead_times_d2);mtx_rmse(:,:,4)=WRF_d1_rmse_20(:,analogs_lead_times_d1)
    mtx_spread(:,1)=ETA_spread_20(:,analogs_lead_times_d3(lead_time_match_idx));mtx_spread(:,:,2)=WRF_d3_spread_20(:,analogs_lead_times_d3(lead_time_match_idx));mtx_spread(:,:,3)=WRF_d2_spread_20(:,analogs_lead_times_d2);mtx_spread(:,:,4)=WRF_d1_spread_20(:,analogs_lead_times_d1)
    plot_width=2.5        
    subplot(2,2,1)
    plot_vector=[1 2 3 4 6 7 8 9]
    [m n] =size(mtx_rmse);
             for i=1 % for number of models consideres 
                plotmtx=mtx_rmse(plot_vector,i);p=plot(plotmtx,['-' Namelist{5}.markers(i) Namelist{5}.color{7+i}],'lineWidth',plot_width);
                hold on;
                plotmtx=mtx_spread(plot_vector,i);p=plot(plotmtx,[':' Namelist{5}.markers(i) Namelist{5}.color{7+i}],'LineWidth',plot_width);
                hold on
               end
                grid on;ylabel('RMSE','fontsize',Namelist{7}.fontsize_sub_plot);
                xlabel('Leadtime','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.10 0.30],'xticklabel',analogs_lead_times_d3(lead_time_match_idx([1 2 3 4 6 7 8 9])));
                legend({'ETA-RMSE','ETA-Spread'})

    subplot(2,2,2)
    [m n] =size(mtx_rmse);
             for i=2 % for number of models consideres 
                plotmtx=mtx_rmse(plot_vector,i);p=plot(plotmtx,['-' Namelist{5}.markers(i) Namelist{5}.color{7+i}],'LineWidth',plot_width);
                hold on;
                plotmtx=mtx_spread(plot_vector,i);p=plot(plotmtx,[':' Namelist{5}.markers(i) Namelist{5}.color{7+i}],'LineWidth',plot_width);
                hold on
               end
                grid on;ylabel('RMSE','fontsize',Namelist{7}.fontsize_sub_plot);
                xlabel('Leadtime','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.10 0.30],'xticklabel',analogs_lead_times_d3(lead_time_match_idx([1 2 3 4 6 7 8 9])));
                legend({'WRF-domaine 3 rmse','WRF-domaine 3 spread'})

    subplot(2,2,3)
    [m n] =size(mtx_rmse);
             for i=3 % for number of models consideres 
                plotmtx=mtx_rmse(plot_vector,i);p=plot(plotmtx,['-' Namelist{5}.markers(i) Namelist{5}.color{7+i}],'LineWidth',plot_width);
                hold on;
                plotmtx=mtx_spread(plot_vector,i);p=plot(plotmtx,[':' Namelist{5}.markers(i) Namelist{5}.color{7+i}],'LineWidth',plot_width);
                hold on
               end
                grid on;ylabel('RMSE','fontsize',Namelist{7}.fontsize_sub_plot);
                xlabel('Leadtime','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.10 0.30],'xticklabel',analogs_lead_times_d3(lead_time_match_idx([1 2 3 4 6 7 8 9])));
                legend({'WRF-domaine 2 rmse','WRF-domaine 2 spread'})

    subplot(2,2,4)
    [m n] =size(mtx_rmse);
             for i=4 % for number of models consideres 
                plotmtx=mtx_rmse(plot_vector,i);p=plot(plotmtx,['-' Namelist{5}.markers(i) Namelist{5}.color{7+i}],'LineWidth',plot_width);
                hold on;
                plotmtx=mtx_spread(plot_vector,i);p=plot(plotmtx,[':' Namelist{5}.markers(i) Namelist{5}.color{7+i}],'LineWidth',plot_width);
                hold on
               end
                grid on;ylabel('RMSE','fontsize',Namelist{7}.fontsize_sub_plot);
                xlabel('Leadtime','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.10 0.30],'xticklabel',analogs_lead_times_d3(lead_time_match_idx([1 2 3 4 6 7 8 9])));
                legend({'WRF-domaine 1 rmse','WRF-domaine 1 spread'})

        maximize
        save_dir=[Namelist{1}.stat_plot_dir,'\prob-plots']
        plot_filename=['\dispersion_diagran_20_analogs_wrf_shear_turbine']
                if isdir(save_dir)
                   saveas(gcf,[save_dir plot_filename] ,'fig')
                   saveas(gcf,[save_dir plot_filename] ,'jpeg')

                else
                    mkdir(save_dir)
                    saveas(gcf,[save_dir plot_filename] ,'fig')
                    saveas(gcf,[save_dir plot_filename] ,'jpeg')

                end
end % turbine Counter




