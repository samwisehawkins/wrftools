
Namelist{1}.root_dir='/home/jepn/work/An_En_RA'
addpath(genpath([Namelist{1}.root_dir '/code/Input']))
addpath(genpath([Namelist{1}.root_dir '/code/functions_matlab']))
%addpath(genpath('C:/Users/jnini/MATLAB/maximize_stuff'))


[ Namelist ]=set_Namelist_forecast_Ray_wind_farm( );

%Cockpitt controls 
    %get_data_flag=1
    produce_power_forecast_time_serie_flag=1

% postprocessing 
    
    do_all_stat_flag=0
    do_single_stat_flag=0
    do_filtering_analysis_flag=0
    do_turbine_by_turbine_stat_flag=0
    do_cost_loss_analysis_flag=0
    do_accuracy_nwp_analysis_flag=0
    do_accuracy_predictor_analysis_flag=0
    do_accuracy_domaine_analysis_flag=0
    do_accuracy_tuning_analysis_flag=0
    do_accuracy_nwp_analysis_all_domaines_on_leadtimes_flag=0
    do_accuracy_concanated_turbines_flag=0
    do_accuracy_concanated_turbines_benchmarking_10_analogs_flag=1
    do_dispersion_diagram_concanated_turbines_flag=0
    
    do_10_analogs_dispersion_diagram_concanated_turbines_flag=0
    do_15_analogs_dispersion_diagram_concanated_turbines_flag=0
    do_05_analogs_dispersion_diagram_concanated_turbines_flag=0
    do_roc_stat_flag=0
    do_rank_histogram_flag=0
    do_reliabilty_diagram_flag=1
    get_regression_constants_flag=0
    do_linear_regresion_based_power_forecast=0
    Make_EPS_time_series_flag=0
    plot_distributions_flag =1           
    
switch 1
    %case get_data_flag
    %get data part 
       % [data_set]=load_data_En_An_RA(Namelist)    
    case produce_power_forecast_time_serie_flag
        [data_set]=load_data_En_An_RA(Namelist)
        num_valid_date=get_num_valid_dates(data_set);
        num_init_date=get_num_init_dates(data_set);
%        cd('/home/jepn/work/An_En_RA/code/functions_matlab/Namelists/experiments/tuning')
		% try different set of predictors weights periods etc
	  cd('/home/jepn/work/An_En_RA/code/functions_matlab/Namelists/experiments/benchmarking')
                % try different set of predictors weights periods etc

       for exp_nr=1:3
           switch 1
               case exp_nr==1
                    [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_AAA( )
                case exp_nr==2
                    [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_ABA( )
                case exp_nr==3
                    [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_ACA( )
               case exp_nr==4
                    [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_BAA( )
                case exp_nr==5
                     [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_BBA( )
                case exp_nr==6
                            [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_BCA( )
                case exp_nr==7
                            [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_CCA( )
                case exp_nr==8
                            [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_CBA( )
                case exp_nr==9
                            [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_CAA( )
		 case exp_nr==10
                    [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_DAA( )
                case exp_nr==11
                    [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_DBA( )
                case exp_nr==12
                    [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_DCA( )
               case exp_nr==13
                    [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_EAA( )
                case exp_nr==14
                     [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_EBA( )
                case exp_nr==15
                            [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_ECA( )

     		 case exp_nr==16
                    [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_FAA( )
                case exp_nr==17
                    [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_FBA( )
                case exp_nr==18
                    [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_FCA( )
               case exp_nr==19
                    [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_GAA( )
                case exp_nr==20
                     [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_GBA( )
                case exp_nr==21
                            [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_GCA( )
                 case exp_nr==22
                    [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_HAA( )
                case exp_nr==23
                     [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_HBA( )
                case exp_nr==24
                            [ Namelist ]=set_Namelist_forecast_Ray_wind_farm_HCA( )
    
        end %switch
               Namelist{5}.Analog.number_of_analogs_search_for=30
               if not(isdir([Namelist{1}.workspace_data_dir_out,'/experiments/',Namelist{1}.experiment]))
                    mkdir([Namelist{1}.workspace_data_dir_out,'/experiments/',Namelist{1}.experiment])
                    save_file=[Namelist{1}.workspace_data_dir_out,'/experiments/',Namelist{1}.experiment,'/Wind_TS_nr_analogs_',num2str(Namelist{5}.Analog.number_of_analogs_search_for)]
                else
                    save_file=[Namelist{1}.workspace_data_dir_out,'/experiments/',Namelist{1}.experiment,'/Wind_TS_nr_analogs_',num2str(Namelist{5}.Analog.number_of_analogs_search_for)]
                end 
                first_time=1;close all hidden;close all force
                display(strcat('Training period period from: ',Namelist{5}.start_analog_search_period' to: ',Namelist{5}.end_analog_search_period) )
                n_end=datenum(Namelist{5}.end_forecast_period,Namelist{1}.datstr_turbine_input_format);
                n_begin=datenum(Namelist{5}.start_forecast_period,Namelist{1}.datstr_turbine_input_format)
                length_forcast_period=n_end-n_begin;waitbar(0,'Initializing waitbar...');
                training_data_set=sub_set_data_set(Namelist,data_set,num_valid_date)
                if exist('turbine_time_series');clear turbine_time_series
                end
                time_serie_winds=cell(2,18);
                while datenum(Namelist{5}.end_forecast_period,Namelist{1}.datstr_turbine_input_format)>...
                         datenum(Namelist{5}.Analog.now,Namelist{1}.datstr_turbine_input_format)
                     %get new forcast vector get new observation verifering the
                     %same datetime and get the analog dates
                       datenum(Namelist{5}.Analog.now,Namelist{1}.datstr_turbine_input_format);
                       n_now=datenum(Namelist{5}.Analog.now,Namelist{1}.datstr_turbine_input_format);
                     %  waitbar(((n_end-n_now)/length_forcast_period),['Resource assesment:',Namelist{4}.nwp_model{1}, ' run: ',Namelist{5}.Analog.now,' and ',num2str(Namelist{5}.Analog.number_of_analogs_search_for),' Analogs' ]);
                       forecast_vector=get_forecast_vector(Namelist,data_set,num_init_date);
                       wind_obs=get_wind_obs(data_set,Namelist,n_now,num_valid_date);
                       
                       switch 1
                            case Namelist{10}.nwp_to_power_forecast_method==0 % resource
                                   [winds weights]=match_forecast_Resorce_assesment(forecast_vector,Namelist,training_data_set);
                            case or(Namelist{10}.nwp_to_power_forecast_method==2,Namelist{10}.nwp_to_power_forecast_method==2) % )
                                dates_analog=get_dates_analog(Namelist,forecast_vector,data_set);
                        end % switch
                        time_serie_winds=get_time_serie_wind(time_serie_winds,forecast_vector,Namelist,first_time,wind_obs,winds,weights);
                        %plot_succes=plot_power_forecast(time_serie_power_forecast_20_analogs_light_filtered_and_banned,power_obs_vector,Namelist);
                        % update now 
                        Namelist{5}.Analog.now=datestr(addtodate(datenum(Namelist{5}.Analog.now,Namelist{1}.datstr_turbine_input_format),1, 'hour'),Namelist{1}.datstr_turbine_input_format);
                        first_time=0;
                  end % while
                  save(save_file,'time_serie_winds')
                  Namelist{5}.Analog.now=Namelist{5}.start_forecast_period;
       end %for exp_nr
       
               % fast tjeck
               plot(time_serie_winds{2,2},'b');hold on
               plot(time_serie_winds{2,21},'r'); hold on
               plot(time_serie_winds{2,20},'g');legend({'analog predictions','observations','raw nwp prediction'});grid on
               
    case plot_distributions_flag 
        plot_distributions(Namelist,save_file)
    case do_all_stat_flag
           if exist('time_serie_power_forecast_25_analogs')
           else
            data_path=[Namelist{1}.workspace_data_dir_out '/' 'Analog_nr_experiment_05_10_15_20_25']
            load(data_path) 
           end
           
          idx_non_nan=find(~isnan(time_serie_power_forecast_05_analogs{2,15}))
          obs=time_serie_power_forecast_05_analogs{2,15}(idx_non_nan);
            [model_ANALOG_5 model_ANALOG_10 model_ANALOG_15 model_ANALOG_20 model_ANALOG_25 ]=get_time_series_anlalogs(time_serie_power_forecast_05_analogs, time_serie_power_forecast_10_analogs, time_serie_power_forecast_15_analogs, time_serie_power_forecast_20_analogs, time_serie_power_forecast_25_analogs,idx_non_nan); 
            [rmse_05 bias_05 crmse_05] = RMSEdecomp_all(obs, model_ANALOG_5)
            [rmse_10 bias_10 crmse_10] = RMSEdecomp_all(obs, model_ANALOG_10)
            [rmse_15 bias_15 crmse_15] = RMSEdecomp_all(obs, model_ANALOG_15)
            [rmse_20 bias_20 crmse_20] = RMSEdecomp_all(obs, model_ANALOG_20)
            [rmse_25 bias_25 crmse_25] = RMSEdecomp_all(obs, model_ANALOG_25)
            stairs([rmse_05,rmse_10,rmse_15,rmse_20,rmse_25])
            do_prob_stat(time_serie_power_forecast_05_analogs,time_serie_power_forecast_10_analogs,time_serie_power_forecast_15_analogs,time_serie_power_forecast_20_analogs,time_serie_power_forecast_25_analogs);  
            
           %NR_ANALOG_SESITIVITY STUDY 
    case do_single_stat_flag==1
        if exist('time_serie_power_forecast_15_analogs_light_filtered_and_banned')
        else
            data_path=[Namelist{1}.workspace_data_dir_out '/' 'Analog_nr_15_light_filtered_and_banned'];
            load(data_path) ;
        end
        if exist('time_serie_power_forecast_15_analogs')
           else
            data_path=[Namelist{1}.workspace_data_dir_out '/' 'analog_nr_15_']
            load(data_path) 
           end
          do_single_prob_stat(time_serie_power_forecast_10_analogs_light_filtered_and_banned,time_serie_power_forecast_10_analogs);  
    case do_filtering_analysis_flag
        do_filtering_analysis(Namelist)
    case do_turbine_by_turbine_stat_flag
    case do_cost_loss_analysis_flag
        do_cost_loss_analysis(Namelist)
    succes=do_turbine_by_turbine_stat(Namelist)   
    case do_accuracy_nwp_analysis_flag
        do_accuracy_nwp_analysis_all_domaines(Namelist)
        
    case do_accuracy_domaine_analysis_flag
        do_accuracy_domaine_analysis( Namelist )
    case do_accuracy_tuning_analysis_flag
        do_accuracy_tuning_analysis(Namelist)
    case do_accuracy_nwp_analysis_all_domaines_on_leadtimes_flag
        do_accuracy_nwp_analysis_all_domaines_on_leadtimes(Namelist)
    case do_accuracy_concanated_turbines_flag
        do_accuracy_concanated_turbines(Namelist)
    case do_accuracy_concanated_turbines_benchmarking_10_analogs_flag
        do_accuracy_concanated_turbines_benchmarking_10_analogs(Namelist)
    case do_dispersion_diagram_concanated_turbines_flag
        do_dispersion_diagram_concanated_turbines(Namelist)
    case do_10_analogs_dispersion_diagram_concanated_turbines_flag
        do_dispersion_diagram_concanated_turbines_10_analogs(Namelist)
    case do_15_analogs_dispersion_diagram_concanated_turbines_flag
        do_dispersion_diagram_concanated_turbines_15_analogs(Namelist)
    case do_05_analogs_dispersion_diagram_concanated_turbines_flag
        do_dispersion_diagram_concanated_turbines_05_analogs(Namelist)
    case do_roc_stat_flag
        counter=0;
        for analogs=[ 5 10 15 20 ]
            counter=counter+1
            [hit_rate,false_alarm_rate]=do_roc_diagram_eta(Namelist,analogs)
            ss_roc_eta(counter,:)=do_skil_score_roc_plot(hit_rate,false_alarm_rate,Namelist,'ETA',3)
        
            [hit_rate,false_alarm_rate]=do_roc_diagram_WRF_d3(Namelist,analogs)
            ss_roc_wrf_d3(counter,:)=do_skil_score_roc_plot(hit_rate,false_alarm_rate,Namelist,'WRF',3)
            [hit_rate,false_alarm_rate]=do_roc_diagram_WRF_d2(Namelist,analogs)
            ss_roc_wrf_d2(counter,:)=do_skil_score_roc_plot(hit_rate,false_alarm_rate,Namelist,'WRF',2)
            [hit_rate,false_alarm_rate]=do_roc_diagram_WRF_d1(Namelist,analogs)
            ss_roc_wrf_d1(counter,:)=do_skil_score_roc_plot(hit_rate,false_alarm_rate,Namelist,'WRF',1)
            
        end
        plot_ss_roc(ss_roc_eta,ss_roc_wrf_d1,ss_roc_wrf_d2,ss_roc_wrf_d3,Namelist)
    case do_rank_histogram_flag
        model='ETA'
        domaine=1
%        exp_name=['Turbine_by_turbine_winter_1_mslp_wspd_wdir_rho_shear_domaine_',num2str(domaine)]
        exp_name='Turbine_by_turbine_winter_training_12_months_2011'
        analogs=5
        [succes rank_unsorted rank_sorted]=do_rank_histogram( Namelist,model,domaine,exp_name,analogs)
        plot_rank(rank_unsorted,Namelist,model,domaine,exp_name,analogs,'unsorted');
        plot_rank(rank_sorted,Namelist,model,domaine,exp_name,analogs,'sorted');
    case do_reliabilty_diagram_flag
        model='WRF'
        domaine=1
%        exp_name=['Turbine_by_turbine_winter_1_mslp_wspd_wdir_rho_shear_domaine_',num2str(domaine)]
        exp_name=Namelist{1}.experiment
        analogs=10
        do_reliabilty_diagram( Namelist,model,domaine,exp_name,analogs)
    case get_regression_constants_flag
        get_regression_constants(good_turbine_data,time_serie_nwp_forecast,Namelist)
    case Make_EPS_time_series_flag
        turbine_vice_w2p=1
        if turbine_vice_w2p
           Make_EPS_time_series_turbine_vice_w2p(Namelist)
        else
            Make_EPS_time_series(Namelist)
        end
    
end %switch 
exit
%save([Namelist{1}.root_dir '/data/workspace/sprog�_long_1','good_turbine_data','time_serie_nwp_forecast')
