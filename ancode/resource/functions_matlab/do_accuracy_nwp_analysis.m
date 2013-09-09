function [ succes ] = do_accuracy_nwp_analysis( Namelist )
%DO_ACCURACY_NWP_ANALYSIS Summary of this function goes here
%   Detailed explanation goes here
exp_name='Turbine_by_turbine_winter'
exp_name_wrf='Turbine_by_turbine_winter_1_domaine_3'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\ETA\out\experiments\',exp_name]
load([file_path,'\turbine_time_series_for_nr_analogs_5'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [ETA_rmse_05(i) ETA_bias_05(i) ETA_crmse_05(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            ETA_NMAE_05(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
        else
            [ETA_rmse_05(i) ETA_bias_05(i) ETA_crmse_05(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            ETA_NMAE_05(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
        end
   
    end
clear turbine_time_series;

file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
load([file_path,'\turbine_time_series_for_nr_analogs_5'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_rmse_05(i) WRF_bias_05(i) WRF_crmse_05(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_NMAE_05(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
        else
            [WRF_rmse_05(i) WRF_bias_05(i) WRF_crmse_05(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_NMAE_05(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
        end
         mtx_nmae(i,1)=ETA_NMAE_05(i);mtx_nmae(i,2)=WRF_NMAE_05(i)
         mtx_crmse(i,1)=ETA_crmse_05(i);mtx_crmse(i,2)=WRF_crmse_05(i)
         mtx_bias(i,1)=ETA_bias_05(i);mtx_bias(i,2)=WRF_bias_05(i)
         mtx_rmse(i,1)=ETA_rmse_05(i);mtx_rmse(i,2)=WRF_rmse_05(i)
         
         
        
    end
    
    subplot (4,3,1)
    bar(mtx_nmae,'grouped');legend({'ETA','WRF'}),colormap('gray'); 
    grid on;ylabel('% NMAE','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.14 0.18]);
    title('5 analogs WRF-2km ETA')

    subplot (4,3,2)
    bar(mtx_crmse,'grouped');legend({'ETA','WRF'}),colormap('gray'); 
    grid on;ylabel('% CRMSE','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.15 0.25]);
    title('5 analogs WRF-2km ETA')

    subplot (4,3,3)
    bar(mtx_bias,'grouped');legend({'ETA','WRF'}),colormap('gray'); 
    grid on;ylabel('% BIAS','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[-0.04 0.02]);
    title('5 analogs WRF-2km ETA')

    clear turbine_time_series;
    % get the 10 Analogs

file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\ETA\out\experiments\',exp_name]
load([file_path,'\turbine_time_series_for_nr_analogs_10'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [ETA_rmse_10(i) ETA_bias_10(i) ETA_crmse_10(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            ETA_NMAE_10(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
        else
            [ETA_rmse_10(i) ETA_bias_10(i) ETA_crmse_10(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            ETA_NMAE_10(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
        end
   
    end
clear turbine_time_series;

file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
load([file_path,'\turbine_time_series_for_nr_analogs_10'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_rmse_10(i) WRF_bias_10(i) WRF_crmse_10(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_NMAE_10(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
        else
            [WRF_rmse_10(i) WRF_bias_10(i) WRF_crmse_10(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_NMAE_10(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
        end
         mtx_nmae(i,1)=ETA_NMAE_10(i);mtx_nmae(i,2)=WRF_NMAE_10(i)
         mtx_crmse(i,1)=ETA_crmse_10(i);mtx_crmse(i,2)=WRF_crmse_10(i)
         mtx_bias(i,1)=ETA_bias_10(i);mtx_bias(i,2)=WRF_bias_10(i)
         mtx_rmse(i,1)=ETA_rmse_10(i);mtx_rmse(i,2)=WRF_rmse_10(i)
         
    end
    
subplot (4,3,4)
    bar(mtx_nmae,'grouped');legend({'ETA','WRF'}),colormap('gray'); 
    grid on;ylabel('% NMAE','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.14 0.18]);
    title('10 analogs WRF-2km ETA')

subplot (4,3,5)
    bar(mtx_crmse,'grouped');legend({'ETA','WRF'}),colormap('gray'); 
    grid on;ylabel('% CRMSE','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.15 0.25]);
    title('10 analogs WRF-2km ETA')

subplot (4,3,6)
    bar(mtx_bias,'grouped');legend({'ETA','WRF'}),colormap('gray'); 
    grid on;ylabel('% Bias','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[-0.04 0.02]);
    title('10 analogs WRF-2km ETA')

     clear turbine_time_series;
    % get the 15 Analogs

file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\ETA\out\experiments\',exp_name]
load([file_path,'\turbine_time_series_for_nr_analogs_15'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [ETA_rmse_15(i) ETA_bias_15(i) ETA_crmse_15(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            ETA_NMAE_15(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
        else
            [ETA_rmse_15(i) ETA_bias_15(i) ETA_crmse_15(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            ETA_NMAE_15(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
        end
   
    end
clear turbine_time_series;

file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
load([file_path,'\turbine_time_series_for_nr_analogs_15'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_rmse_15(i) WRF_bias_15(i) WRF_crmse_15(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_NMAE_15(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
        else
            [WRF_rmse_15(i) WRF_bias_15(i) WRF_crmse_15(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_NMAE_15(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
        end
         mtx_nmae(i,1)=ETA_NMAE_15(i);mtx_nmae(i,2)=WRF_NMAE_15(i)
         mtx_crmse(i,1)=ETA_crmse_15(i);mtx_crmse(i,2)=WRF_crmse_15(i)
         mtx_bias(i,1)=ETA_bias_15(i);mtx_bias(i,2)=WRF_bias_15(i)
         mtx_rmse(i,1)=ETA_rmse_15(i);mtx_rmse(i,2)=WRF_rmse_15(i)
        
    end
    
subplot (4,3,7)
    bar(mtx_nmae,'grouped');legend({'ETA','WRF'}),colormap('gray'); 
    grid on;ylabel('% NMAE','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.14 0.18]);
    title('15 analogs WRF-2km ETA')

subplot (4,3,8)
    bar(mtx_crmse,'grouped');legend({'ETA','WRF'}),colormap('gray'); 
    grid on;ylabel('% CRMSE','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.15 0.25]);
    title('15 analogs WRF-2km ETA')

subplot (4,3,9)
    bar(mtx_bias,'grouped');legend({'ETA','WRF'}),colormap('gray'); 
    grid on;ylabel('% Bias','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[-0.04 0.02]);
    title('15 analogs WRF-2km ETA')


     clear turbine_time_series;
    % get the 15 Analogs

file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\ETA\out\experiments\',exp_name]
load([file_path,'\turbine_time_series_for_nr_analogs_20'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [ETA_rmse_20(i) ETA_bias_20(i) ETA_crmse_20(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            ETA_NMAE_20(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
        else
            [ETA_rmse_20(i) ETA_bias_20(i) ETA_crmse_20(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            ETA_NMAE_20(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
        end
   
    end
clear turbine_time_series;

file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
load([file_path,'\turbine_time_series_for_nr_analogs_20'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_rmse_20(i) WRF_bias_20(i) WRF_crmse_20(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_NMAE_20(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
        else
            [WRF_rmse_20(i) WRF_bias_20(i) WRF_crmse_20(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_NMAE_20(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
        end
         mtx_nmae(i,1)=ETA_NMAE_20(i);mtx_nmae(i,2)=WRF_NMAE_20(i)
         mtx_crmse(i,1)=ETA_crmse_20(i);mtx_crmse(i,2)=WRF_crmse_20(i)
         mtx_bias(i,1)=ETA_bias_20(i);mtx_bias(i,2)=WRF_bias_20(i)
         mtx_rmse(i,1)=ETA_rmse_20(i);mtx_rmse(i,2)=WRF_rmse_20(i)
        
    end
    
subplot (4,3,10)
    bar(mtx_nmae,'grouped');legend({'ETA','WRF'}),colormap('gray'); 
    grid on;ylabel('% NMAE','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.14 0.18]);
    title('20 analogs WRF-2km ETA')
subplot (4,3,11)
    bar(mtx_crmse,'grouped');legend({'ETA','WRF'}),colormap('gray'); 
    grid on;ylabel('% CRMSE','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.15 0.25]);
    title('20 analogs WRF-2km ETA')

subplot (4,3,12)
    bar(mtx_bias,'grouped');legend({'ETA','WRF'}),colormap('gray'); 
    grid on;ylabel('% Bias','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[-0.04 0.02]);
    title('20 analogs WRF-2km ETA')
    
    maximize
    save_dir=[Namelist{1}.stat_plot_dir,'\accuracy_nwp']
    plot_filename='\NMAE_crmse_bias_on_nr_analogs_nwp_domaine_3.fig'
            if isdir(save_dir)
               saveas(gcf,[save_dir plot_filename] ,'fig')
               saveas(gcf,[save_dir plot_filename] ,'jpeg')
               
            else
                mkdir(save_dir)
                saveas(gcf,[save_dir plot_filename] ,'fig')
                saveas(gcf,[save_dir plot_filename] ,'jpeg')
               
            end
    end
    
    


