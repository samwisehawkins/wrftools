function [ succes ] = do_accuracy_tuning_analysis( Namelist )
%DO_ACCURACY_NWP_ANALYSIS Summary of this function goes here
%   Detailed explanation goes here
exp_name='Turbine_by_turbine_winter_1_domaine_3'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name]
load([file_path,'\turbine_time_series_for_nr_analogs_10'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_rmse_10_no_shear(i) WRF_bias_10_no_shear(i) WRF_crmse_10_no_shear(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_NMAE_10_no_shear(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
        else
            [WRF_rmse_10_no_shear(i) WRF_bias_10_no_shear(i) WRF_crmse_10_no_shear(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_NMAE_10_no_shear(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
        end
         mtx_nmae(i,1)=WRF_NMAE_10_no_shear(i); 
    end
    clear turbine_time_series

exp_name='Turbine_by_turbine_winter_1_mslp_wspd_wdir_rho_shear_domaine_3'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name]
load([file_path,'\turbine_time_series_for_nr_analogs_10'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_rmse_10_shear(i) WRF_bias_10_shear(i) WRF_crmse_10_shear(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_NMAE_10_shear(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
        else
            [WRF_rmse_10_shear(i) WRF_bias_10_shear(i) WRF_crmse_10_shear(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_NMAE_10_shear(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
        end
         mtx_nmae(i,2)=WRF_NMAE_10_shear(i); 
    end
    clear turbine_time_series
subplot(3,1,1)

    bar(mtx_nmae,'grouped');legend({'no shear','shear'}),colormap('gray'); 
    grid on;ylabel('NMAE','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.14 0.18 ]);
    title('10 analogs');maximize

    exp_name='Turbine_by_turbine_winter_1_domaine_3'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name]
load([file_path,'\turbine_time_series_for_nr_analogs_15'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_rmse_15_no_shear(i) WRF_bias_15_no_shear(i) WRF_crmse_15_no_shear(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_NMAE_15_no_shear(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
        else
            [WRF_rmse_15_no_shear(i) WRF_bias_15_no_shear(i) WRF_crmse_15_no_shear(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_NMAE_15_no_shear(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
        end
         mtx_nmae(i,1)=WRF_NMAE_15_no_shear(i); 
    end
    clear turbine_time_series

exp_name='Turbine_by_turbine_winter_1_mslp_wspd_wdir_rho_shear_domaine_3'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name]
load([file_path,'\turbine_time_series_for_nr_analogs_15'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_rmse_15_shear(i) WRF_bias_15_shear(i) WRF_crmse_15_shear(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_NMAE_15_shear(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
        else
            [WRF_rmse_15_shear(i) WRF_bias_15_shear(i) WRF_crmse_15_shear(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_NMAE_15_shear(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
        end
         mtx_nmae(i,2)=WRF_NMAE_15_shear(i); 
    end
    clear turbine_time_series

subplot(3,1,2)
    bar(mtx_nmae,'grouped');legend({'no shear','shear'}),colormap('gray'); 
    grid on;ylabel('NMAE','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.14 0.18 ]);
    title('15 analogs');maximize

exp_name='Turbine_by_turbine_winter_1_domaine_3'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name]
load([file_path,'\turbine_time_series_for_nr_analogs_20'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_rmse_20_no_shear(i) WRF_bias_20_no_shear(i) WRF_crmse_20_no_shear(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_NMAE_20_no_shear(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
        else
            [WRF_rmse_20_no_shear(i) WRF_bias_20_no_shear(i) WRF_crmse_20_no_shear(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_NMAE_20_no_shear(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
        end
         mtx_nmae(i,1)=WRF_NMAE_20_no_shear(i); 
    end
    clear turbine_time_series

exp_name='Turbine_by_turbine_winter_1_mslp_wspd_wdir_rho_shear_domaine_3'
file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\WRF\out\experiments\',exp_name]
load([file_path,'\turbine_time_series_for_nr_analogs_20'])
% gets the index where obervation are not missing for each turbine 
[m n]=size(turbine_time_series)    
    for i=1:n
        good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value)
        if Namelist{10}.normalize_errors
            [WRF_rmse_20_shear(i) WRF_bias_20_shear(i) WRF_crmse_20_shear(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw, turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw);
            WRF_NMAE_20_shear(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i}))/Namelist{10}.rated_capasity_kw)
        else
            [WRF_rmse_20_shear(i) WRF_bias_20_shear(i) WRF_crmse_20_shear(i)] = RMSEdecomp_all(turbine_time_series(1,i).data{2,15}(good_idx{i}), turbine_time_series(1,i).data{2,2}(good_idx{i}));
            WRF_NMAE_20_shear(i)=mean(abs(turbine_time_series(1,i).data{2,15}(good_idx{i})-turbine_time_series(1,i).data{2,2}(good_idx{i})))
        end
         mtx_nmae(i,2)=WRF_NMAE_20_shear(i); 
    end
    clear turbine_time_series

subplot(3,1,3)
    bar(mtx_nmae,'grouped');legend({'no shear','shear'}),colormap('gray'); 
    grid on;ylabel('NMAE','fontsize',Namelist{7}.fontsize_sub_plot);
    xlabel('turbine','fontsize',Namelist{7}.fontsize_sub_plot);set(gca,'fontsize',Namelist{7}.fontsize_sub_plot,'ylim',[0.14 0.18 ]);
    title('20 analogs');maximize
