function [ succes ] = do_accuracy_nwp_analysis_all_domaines( Namelist )
%DO_ACCURACY_NWP_ANALYSIS Summary of this function goes here
%   Detailed explanation goes here
exp_name='Turbine_by_turbine_winter_training_12_months_2011'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\ETA\out\experiments\',exp_name]
load([file_path,'\turbine_time_series_for_nr_analogs_5'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [ETA_rmse_05(i) ETA_bias_05(i) ETA_crmse_05(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            ETA_NMAE_05(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
            ETA_pearson_05(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            ETA_spearman_rank_correltion_05(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        else
            [ETA_rmse_05(i) ETA_bias_05(i) ETA_crmse_05(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            ETA_NMAE_05(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
            ETA_pearson_05(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            ETA_spearman_rank_correltion_05(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        end
   
    end
clear turbine_time_series;


exp_name_wrf='Turbine_by_turbine_winter_1_mslp_wspd_wdir_rho_shear_domaine_3'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
load([file_path,'\turbine_time_series_for_nr_analogs_5'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_d3_rmse_05(i) WRF_d3_bias_05(i) WRF_d3_crmse_05(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_d3_NMAE_05(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
            WRF_d3_pearson_05(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d3_spearman_rank_correltion_05(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        else
            [WRF_d3_rmse_05(i) WRF_d3_bias_05(i) WRF_d3_crmse_05(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_d3_NMAE_05(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
            WRF_d3_pearson_05(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d3_spearman_rank_correltion_05(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        end
    end    
exp_name_wrf='Turbine_by_turbine_winter_1_mslp_wspd_wdir_rho_shear_domaine_2'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
load([file_path,'\turbine_time_series_for_nr_analogs_5'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_d2_rmse_05(i) WRF_d2_bias_05(i) WRF_d2_crmse_05(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_d2_NMAE_05(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
            WRF_d2_pearson_05(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d2_spearman_rank_correltion_05(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        else
            [WRF_d2_rmse_05(i) WRF_d2_bias_05(i) WRF_d2_crmse_05(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_d2_NMAE_05(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
            WRF_d2_pearson_05(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d2_spearman_rank_correltion_05(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        end
    end 
exp_name_wrf='Turbine_by_turbine_winter_1_mslp_wspd_wdir_rho_shear_domaine_1'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
load([file_path,'\turbine_time_series_for_nr_analogs_5'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_d1_rmse_05(i) WRF_d1_bias_05(i) WRF_d1_crmse_05(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_d1_NMAE_05(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
            WRF_d1_pearson_05(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d1_spearman_rank_correltion_05(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        else
            [WRF_d1_rmse_05(i) WRF_d1_bias_05(i) WRF_d1_crmse_05(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_d1_NMAE_05(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
            WRF_d1_pearson_05(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d1_spearman_rank_correltion_05(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        end
        
        
         mtx_nmae(i,1)=ETA_NMAE_05(i);mtx_nmae(i,2)=WRF_d3_NMAE_05(i);mtx_nmae(i,3)=WRF_d2_NMAE_05(i);mtx_nmae(i,4)=WRF_d1_NMAE_05(i)
         mtx_crmse(i,1)=ETA_crmse_05(i);mtx_crmse(i,2)=WRF_d3_crmse_05(i);mtx_crmse(i,3)=WRF_d2_crmse_05(i);mtx_crmse(i,4)=WRF_d1_crmse_05(i)
         mtx_bias(i,1)=ETA_bias_05(i);mtx_bias(i,2)=WRF_d3_bias_05(i);mtx_bias(i,3)=WRF_d2_bias_05(i);mtx_bias(i,4)=WRF_d1_bias_05(i)
         mtx_rmse(i,1)=ETA_rmse_05(i);mtx_rmse(i,2)=WRF_d3_rmse_05(i);mtx_rmse(i,3)=WRF_d2_rmse_05(i);mtx_rmse(i,4)=WRF_d1_rmse_05(i)
         mtx_pearson(i,1)=ETA_pearson_05(i);mtx_pearson(i,2)=WRF_d3_pearson_05(i);mtx_pearson(i,3)=WRF_d2_pearson_05(i);mtx_pearson(i,4)=WRF_d1_pearson_05(i)
         mtx_spearman_rank_correltion(i,1)=ETA_spearman_rank_correltion_05(i);mtx_spearman_rank_correltion(i,2)=WRF_d3_spearman_rank_correltion_05(i);mtx_spearman_rank_correltion(i,3)=WRF_d2_spearman_rank_correltion_05(i);mtx_spearman_rank_correltion(i,4)=WRF_d1_spearman_rank_correltion_05(i)
         
         
        
    end
    
    subplot (4,5,1)
    bar(mtx_nmae,'grouped');colormap('gray'); 
    grid on;ylabel('NMAE','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.14 0.18]);
    
    subplot (4,5,2)
    bar(mtx_crmse,'grouped');colormap('gray'); 
    grid on;ylabel('CRMSE','fontsize',Namelist{7}.fontsize_sub_plot);
    set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.15 0.25]);
    
    subplot (4,5,3)
    bar(mtx_bias,'grouped');colormap('gray'); 
    grid on;ylabel('BIAS','fontsize',Namelist{7}.fontsize_sub_plot);
    set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[-0.04 0.02]);
    title('5 analogs WRF-ETA')

    subplot (4,5,4)
    bar(mtx_pearson,'grouped');colormap('gray'); 
    grid on;ylabel('Cor pearson','fontsize',Namelist{7}.fontsize_sub_plot);
    set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.45,0.75]);
    
    subplot (4,5,5)
    bar(mtx_spearman_rank_correltion,'grouped');colormap('gray'); 
    grid on;ylabel('Spearman','fontsize',Namelist{7}.fontsize_sub_plot);
    set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.45,0.75]);
    
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
            ETA_pearson_10(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            ETA_spearman_rank_correltion_10(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        else
            [ETA_rmse_10(i) ETA_bias_10(i) ETA_crmse_10(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            ETA_NMAE_10(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
            ETA_pearson_10(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            ETA_spearman_rank_correltion_10(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        end
   
    end
    
    clear turbine_time_series;

exp_name_wrf='Turbine_by_turbine_winter_1_domaine_3'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
load([file_path,'\turbine_time_series_for_nr_analogs_10'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_d3_rmse_10(i) WRF_d3_bias_10(i) WRF_d3_crmse_10(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_d3_NMAE_10(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
            WRF_d3_pearson_10(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d3_spearman_rank_correltion_10(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        else
            [WRF_d3_rmse_10(i) WRF_d3_bias_10(i) WRF_d3_crmse_10(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_d3_NMAE_10(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
            WRF_d3_pearson_10(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d3_spearman_rank_correltion_10(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        end
    end    
exp_name_wrf='Turbine_by_turbine_winter_1_domaine_2'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
load([file_path,'\turbine_time_series_for_nr_analogs_10'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_d2_rmse_10(i) WRF_d2_bias_10(i) WRF_d2_crmse_10(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_d2_NMAE_10(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
            WRF_d2_pearson_10(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d2_spearman_rank_correltion_10(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        else
            [WRF_d2_rmse_10(i) WRF_d2_bias_10(i) WRF_d2_crmse_10(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_d2_NMAE_10(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
            WRF_d2_pearson_10(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d2_spearman_rank_correltion_10(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        end
    end 
exp_name_wrf='Turbine_by_turbine_winter_1_domaine_1'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
load([file_path,'\turbine_time_series_for_nr_analogs_10'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_d1_rmse_10(i) WRF_d1_bias_10(i) WRF_d1_crmse_10(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_d1_NMAE_10(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
            WRF_d1_pearson_10(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d1_spearman_rank_correltion_10(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        else
            [WRF_d1_rmse_10(i) WRF_d1_bias_10(i) WRF_d1_crmse_10(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_d1_NMAE_10(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
            WRF_d1_pearson_10(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d1_spearman_rank_correltion_10(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        end
        
        
         mtx_nmae(i,1)=ETA_NMAE_10(i);mtx_nmae(i,2)=WRF_d3_NMAE_10(i);mtx_nmae(i,3)=WRF_d2_NMAE_10(i);mtx_nmae(i,4)=WRF_d1_NMAE_10(i)
         mtx_crmse(i,1)=ETA_crmse_10(i);mtx_crmse(i,2)=WRF_d3_crmse_10(i);mtx_crmse(i,3)=WRF_d2_crmse_10(i);mtx_crmse(i,4)=WRF_d1_crmse_10(i)
         mtx_bias(i,1)=ETA_bias_10(i);mtx_bias(i,2)=WRF_d3_bias_10(i);mtx_bias(i,3)=WRF_d2_bias_10(i);mtx_bias(i,4)=WRF_d1_bias_10(i)
         mtx_rmse(i,1)=ETA_rmse_10(i);mtx_rmse(i,2)=WRF_d3_rmse_10(i);mtx_rmse(i,3)=WRF_d2_rmse_10(i);mtx_rmse(i,4)=WRF_d1_rmse_10(i)
         mtx_pearson(i,1)=ETA_pearson_10(i);mtx_pearson(i,2)=WRF_d3_pearson_10(i);mtx_pearson(i,3)=WRF_d2_pearson_10(i);mtx_pearson(i,4)=WRF_d1_pearson_10(i)
         mtx_spearman_rank_correltion(i,1)=ETA_spearman_rank_correltion_10(i);mtx_spearman_rank_correltion(i,2)=WRF_d3_spearman_rank_correltion_10(i);mtx_spearman_rank_correltion(i,3)=WRF_d2_spearman_rank_correltion_10(i);mtx_spearman_rank_correltion(i,4)=WRF_d1_spearman_rank_correltion_10(i)
         
    end
    
    
subplot (4,5,6)
    bar(mtx_nmae,'grouped');colormap('gray'); 
    grid on;ylabel('NMAE','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.14 0.18]);
    
subplot (4,5,7)
    bar(mtx_crmse,'grouped');colormap('gray'); 
    grid on;ylabel('CRMSE','fontsize',Namelist{7}.fontsize_sub_plot);
    set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.15 0.25]);
    
 subplot (4,5,8)
    bar(mtx_bias,'grouped');colormap('gray');
    grid on;ylabel('BIAS','fontsize',Namelist{7}.fontsize_sub_plot);
    set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[-0.04 0.02]);
    title('10 analogs WRF-ETA')

 subplot (4,5,9)
    bar(mtx_pearson,'grouped');colormap('gray'); 
    grid on;ylabel('Cor pearson','fontsize',Namelist{7}.fontsize_sub_plot);
    set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.45,0.75]);
    
    subplot (4,5,10)
    bar(mtx_spearman_rank_correltion,'grouped');colormap('gray'); 
    grid on;ylabel('Spearman','fontsize',Namelist{7}.fontsize_sub_plot);
    set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.45,0.75]);
    


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
            ETA_pearson_15(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            ETA_spearman_rank_correltion_15(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        else
            [ETA_rmse_15(i) ETA_bias_15(i) ETA_crmse_15(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            ETA_NMAE_15(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
            ETA_pearson_15(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            ETA_spearman_rank_correltion_15(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        end
   
    end
clear turbine_time_series;

exp_name_wrf='Turbine_by_turbine_winter_1_domaine_3'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
load([file_path,'\turbine_time_series_for_nr_analogs_15'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_d3_rmse_15(i) WRF_d3_bias_15(i) WRF_d3_crmse_15(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_d3_NMAE_15(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
            WRF_d3_pearson_15(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d3_spearman_rank_correltion_15(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        else
            [WRF_d3_rmse_15(i) WRF_d3_bias_15(i) WRF_d3_crmse_15(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_d3_NMAE_15(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
            WRF_d3_pearson_15(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d3_spearman_rank_correltion_15(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        end
    end    
exp_name_wrf='Turbine_by_turbine_winter_1_domaine_2'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
load([file_path,'\turbine_time_series_for_nr_analogs_15'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_d2_rmse_15(i) WRF_d2_bias_15(i) WRF_d2_crmse_15(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_d2_NMAE_15(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
            WRF_d2_pearson_15(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d2_spearman_rank_correltion_15(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        else
            [WRF_d2_rmse_15(i) WRF_d2_bias_15(i) WRF_d2_crmse_15(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_d2_NMAE_15(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
            WRF_d2_pearson_15(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d2_spearman_rank_correltion_15(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        end
    end 
exp_name_wrf='Turbine_by_turbine_winter_1_domaine_1'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
load([file_path,'\turbine_time_series_for_nr_analogs_15'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_d1_rmse_15(i) WRF_d1_bias_15(i) WRF_d1_crmse_15(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_d1_NMAE_15(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
            WRF_d1_pearson_15(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d1_spearman_rank_correltion_15(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        else
            [WRF_d1_rmse_15(i) WRF_d1_bias_15(i) WRF_d1_crmse_15(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_d1_NMAE_15(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
            WRF_d1_pearson_15(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d1_spearman_rank_correltion_15(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        end
        
        
         mtx_nmae(i,1)=ETA_NMAE_15(i);mtx_nmae(i,2)=WRF_d3_NMAE_15(i);mtx_nmae(i,3)=WRF_d2_NMAE_15(i);mtx_nmae(i,4)=WRF_d1_NMAE_15(i)
         mtx_crmse(i,1)=ETA_crmse_15(i);mtx_crmse(i,2)=WRF_d3_crmse_15(i);mtx_crmse(i,3)=WRF_d2_crmse_15(i);mtx_crmse(i,4)=WRF_d1_crmse_15(i)
         mtx_bias(i,1)=ETA_bias_15(i);mtx_bias(i,2)=WRF_d3_bias_15(i);mtx_bias(i,3)=WRF_d2_bias_15(i);mtx_bias(i,4)=WRF_d1_bias_15(i)
         mtx_rmse(i,1)=ETA_rmse_15(i);mtx_rmse(i,2)=WRF_d3_rmse_15(i);mtx_rmse(i,3)=WRF_d2_rmse_15(i);mtx_rmse(i,4)=WRF_d1_rmse_15(i)
         mtx_pearson(i,1)=ETA_pearson_15(i);mtx_pearson(i,2)=WRF_d3_pearson_15(i);mtx_pearson(i,3)=WRF_d2_pearson_15(i);mtx_pearson(i,4)=WRF_d1_pearson_15(i)
         mtx_spearman_rank_correltion(i,1)=ETA_spearman_rank_correltion_15(i);mtx_spearman_rank_correltion(i,2)=WRF_d3_spearman_rank_correltion_15(i);mtx_spearman_rank_correltion(i,3)=WRF_d2_spearman_rank_correltion_15(i);mtx_spearman_rank_correltion(i,4)=WRF_d1_spearman_rank_correltion_15(i)
         
        
    end

    
subplot (4,5,11)
    bar(mtx_nmae,'grouped');colormap('gray'); 
    grid on;ylabel('NMAE','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.14 0.18]);
   
subplot (4,5,12)
    bar(mtx_crmse,'grouped');colormap('gray'); 
    grid on;ylabel('CRMSE','fontsize',Namelist{7}.fontsize_sub_plot);
    set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.15 0.25]);
   
 subplot (4,5,13)
    bar(mtx_bias,'grouped');colormap('gray'); 
    grid on;ylabel('BIAS','fontsize',Namelist{7}.fontsize_sub_plot);
    ;set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[-0.04 0.02]);
    title('15 analogs WRF-ETA')

subplot (4,5,14)
    bar(mtx_pearson,'grouped');colormap('gray'); 
    grid on;ylabel('Cor pearson','fontsize',Namelist{7}.fontsize_sub_plot);
    set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.45,0.75]);
   
subplot (4,5,15)
    bar(mtx_spearman_rank_correltion,'grouped');colormap('gray'); 
    grid on;ylabel('Spearman','fontsize',Namelist{7}.fontsize_sub_plot);
    set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.45,0.75]);
   
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
            ETA_pearson_20(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            ETA_spearman_rank_correltion_20(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');

        else
            [ETA_rmse_20(i) ETA_bias_20(i) ETA_crmse_20(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            ETA_NMAE_20(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
            ETA_pearson_20(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            ETA_spearman_rank_correltion_20(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        end
   
    end
clear turbine_time_series;

exp_name_wrf='Turbine_by_turbine_winter_1_domaine_3'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
load([file_path,'\turbine_time_series_for_nr_analogs_20'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
           [WRF_d3_rmse_20(i) WRF_d3_bias_20(i) WRF_d3_crmse_20(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_d3_NMAE_20(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
            WRF_d3_pearson_20(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d3_spearman_rank_correltion_20(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');

        else
            [WRF_d3_rmse_20(i) WRF_d3_bias_20(i) WRF_d3_crmse_20(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_d3_NMAE_20(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
            WRF_d3_pearson_20(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d3_spearman_rank_correltion_20(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        end
    end    
exp_name_wrf='Turbine_by_turbine_winter_1_domaine_2'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
load([file_path,'\turbine_time_series_for_nr_analogs_20'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_d2_rmse_20(i) WRF_d2_bias_20(i) WRF_d2_crmse_20(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_d2_NMAE_20(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
            WRF_d2_pearson_20(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d2_spearman_rank_correltion_20(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        else
            [WRF_d2_rmse_20(i) WRF_d2_bias_20(i) WRF_d2_crmse_20(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_d2_NMAE_20(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
            WRF_d2_pearson_20(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d2_spearman_rank_correltion_20(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        end
    end 
exp_name_wrf='Turbine_by_turbine_winter_1_domaine_1'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name_wrf]
load([file_path,'\turbine_time_series_for_nr_analogs_20'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_d1_rmse_20(i) WRF_d1_bias_20(i) WRF_d1_crmse_20(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_d1_NMAE_20(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
            WRF_d1_pearson_20(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d1_spearman_rank_correltion_20(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        else
            [WRF_d1_rmse_20(i) WRF_d1_bias_20(i) WRF_d1_crmse_20(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_d1_NMAE_20(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
            WRF_d1_pearson_20(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Pearson');
            WRF_d1_spearman_rank_correltion_20(i)=corr(turbine_time_series(1,i).data{2,15}(good_idx{i}),turbine_time_series(1,i).data{2,2}(good_idx{i}), 'Type', 'Spearman');
        end
        
        
         mtx_nmae(i,1)=ETA_NMAE_20(i);mtx_nmae(i,2)=WRF_d3_NMAE_20(i);mtx_nmae(i,3)=WRF_d2_NMAE_20(i);mtx_nmae(i,4)=WRF_d1_NMAE_20(i)
         mtx_crmse(i,1)=ETA_crmse_20(i);mtx_crmse(i,2)=WRF_d3_crmse_20(i);mtx_crmse(i,3)=WRF_d2_crmse_20(i);mtx_crmse(i,4)=WRF_d1_crmse_20(i)
         mtx_bias(i,1)=ETA_bias_20(i);mtx_bias(i,2)=WRF_d3_bias_20(i);mtx_bias(i,3)=WRF_d2_bias_20(i);mtx_bias(i,4)=WRF_d1_bias_20(i)
         mtx_rmse(i,1)=ETA_rmse_20(i);mtx_rmse(i,2)=WRF_d3_rmse_20(i);mtx_rmse(i,3)=WRF_d2_rmse_20(i);mtx_rmse(i,4)=WRF_d1_rmse_20(i)
         mtx_pearson(i,1)=ETA_pearson_20(i);mtx_pearson(i,2)=WRF_d3_pearson_20(i);mtx_pearson(i,3)=WRF_d2_pearson_20(i);mtx_pearson(i,4)=WRF_d1_pearson_20(i)
         mtx_spearman_rank_correltion(i,1)=ETA_spearman_rank_correltion_20(i);mtx_spearman_rank_correltion(i,2)=WRF_d3_spearman_rank_correltion_20(i);mtx_spearman_rank_correltion(i,3)=WRF_d2_spearman_rank_correltion_20(i);mtx_spearman_rank_correltion(i,4)=WRF_d1_spearman_rank_correltion_20(i)
        
    end

%plots

    
subplot (4,5,16)
    bar(mtx_nmae,'grouped');colormap('gray'); 
    grid on;ylabel('NMAE','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.14 0.18]);
    
subplot (4,5,17)
    bar(mtx_crmse,'grouped');colormap('gray'); 
    grid on;ylabel('CRMSE','fontsize',Namelist{7}.fontsize_sub_plot);
    set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.15 0.25]);
    
 subplot (4,5,18)
    bar(mtx_bias,'grouped');colormap('gray'); legend({'ETA','WRF-d3','WRF-d2','WRF-d1'},'location','southoutside')
    grid on;ylabel('BIAS','fontsize',Namelist{7}.fontsize_sub_plot);
    set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[-0.04 0.02]);
    title('20 analogs WRF-ETA')
subplot (4,5,19)
    bar(mtx_pearson,'grouped');colormap('gray'); 
    grid on;ylabel('Cor pearson','fontsize',Namelist{7}.fontsize_sub_plot);
    set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.45,0.75]);
    
subplot (4,5,20)
    bar(mtx_spearman_rank_correltion,'grouped');colormap('gray'); 
    grid on;ylabel('Spearman','fontsize',Namelist{7}.fontsize_sub_plot);
    set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.45,0.75]);
    

    maximize
    save_dir=[Namelist{1}.stat_plot_dir,'\accuracy_nwp']
    plot_filename='\pearson_spearman_nmae_crmse_bias_on_nr_analogs_nwp_all_domaines_wrf_shear'
            if isdir(save_dir)
               saveas(gcf,[save_dir plot_filename] ,'fig')
               saveas(gcf,[save_dir plot_filename] ,'jpeg')
               
            else
                mkdir(save_dir)
                saveas(gcf,[save_dir plot_filename] ,'fig')
                saveas(gcf,[save_dir plot_filename] ,'jpeg')
               
            end
    end
    
    


