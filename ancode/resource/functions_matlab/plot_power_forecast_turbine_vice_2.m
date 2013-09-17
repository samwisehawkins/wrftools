function [ Succes ] = plot_power_forecast_turbine_vice_2(time_serie_power_forecast,power_obs_vector,Namelist,last_updated)
%PLOT_POWER_FORECAST Summary of this function goes here
%   Detailed explanation goes here


% to be exchanged with function on forecast work station expect from dave
% part 

close all
[m n]=size(time_serie_power_forecast);
[nr_data_points]=length(Namelist{1,5}.Analog.lead_times)   ;
sum_power=0;sum_percentiles_10=0;sum_percentiles_20=0;sum_percentiles_30=0;sum_percentiles_40=0;...
sum_percentiles_60=0;sum_percentiles_70=0;sum_percentiles_80=0;sum_percentiles_90=0;
for turbine_counter=1:n
    sum_power=sum_power+time_serie_power_forecast(1,turbine_counter).data{2,2}(length(time_serie_power_forecast(1,turbine_counter).data{2,2})-...
              (nr_data_points-1)/Namelist{5}.Analog.lead_delta:length(time_serie_power_forecast(1,turbine_counter).data{2,2}))
    sum_percentiles_10=sum_percentiles_10+time_serie_power_forecast(1,turbine_counter).data{2,3}(length(time_serie_power_forecast(1,turbine_counter).data{2,3})-...
              (nr_data_points-1)/Namelist{5}.Analog.lead_delta:length(time_serie_power_forecast(1,turbine_counter).data{2,3}))
    sum_percentiles_20=sum_percentiles_10+time_serie_power_forecast(1,turbine_counter).data{2,4}(length(time_serie_power_forecast(1,turbine_counter).data{2,4})-...
              (nr_data_points-1)/Namelist{5}.Analog.lead_delta:length(time_serie_power_forecast(1,turbine_counter).data{2,4}))
    sum_percentiles_30=sum_percentiles_30+time_serie_power_forecast(1,turbine_counter).data{2,5}(length(time_serie_power_forecast(1,turbine_counter).data{2,5})-...
               (nr_data_points-1)/Namelist{5}.Analog.lead_delta:length(time_serie_power_forecast(1,turbine_counter).data{2,5}))
   
    sum_percentiles_40=sum_percentiles_40+time_serie_power_forecast(1,turbine_counter).data{2,6}(length(time_serie_power_forecast(1,turbine_counter).data{2,6})-...
              (nr_data_points-1)/Namelist{5}.Analog.lead_delta:length(time_serie_power_forecast(1,turbine_counter).data{2,6}))
    
    sum_percentiles_60=sum_percentiles_60+time_serie_power_forecast(1,turbine_counter).data{2,8}(length(time_serie_power_forecast(1,turbine_counter).data{2,8})-...
              (nr_data_points-1)/Namelist{5}.Analog.lead_delta:length(time_serie_power_forecast(1,turbine_counter).data{2,8}))
    sum_percentiles_70=sum_percentiles_70+time_serie_power_forecast(1,turbine_counter).data{2,9}(length(time_serie_power_forecast(1,turbine_counter).data{2,9})-...
              (nr_data_points-1)/Namelist{5}.Analog.lead_delta:length(time_serie_power_forecast(1,turbine_counter).data{2,9}))
    sum_percentiles_80=sum_percentiles_80+time_serie_power_forecast(1,turbine_counter).data{2,10}(length(time_serie_power_forecast(1,turbine_counter).data{2,10})-...
              (nr_data_points-1)/Namelist{5}.Analog.lead_delta:length(time_serie_power_forecast(1,turbine_counter).data{2,10}))
    sum_percentiles_90=sum_percentiles_90+time_serie_power_forecast(1,turbine_counter).data{2,11}(length(time_serie_power_forecast(1,turbine_counter).data{2,11})-...
              (nr_data_points-1)/Namelist{5}.Analog.lead_delta:length(time_serie_power_forecast(1,turbine_counter).data{2,11}))
                good_obs_idx_1=intersect(find(not(power_obs_vector(1,1).power_obs==-999)),find(not(power_obs_vector(1,2).power_obs==-999)))
                good_obs_idx_2=intersect(find(not(power_obs_vector(1,3).power_obs==-999)),find(not(power_obs_vector(1,4).power_obs==-999)))
                
                if isempty(intersect(good_obs_idx_1,good_obs_idx_2))
                else
                    sum_obs=0;
                    
                    for j=1:length(intersect(good_obs_idx_1,good_obs_idx_2))
                        sum_obs(j)=sum([power_obs_vector(1,je).power_obs])
                    end
                    
                    sum_obs=sum(power_obs_vector(1,1:n).power_obs(intersect(good_obs_idx_1,good_obs_idx_2)))
                    sum_obs=sum(power_obs_vector(1,1:n).power_obs([1 2 3]))
                end
end
sum_percentiles=[sum_percentiles_10 sum_percentiles_20 sum_percentiles_30 sum_percentiles_40 sum_percentiles_60 sum_percentiles_70...
    sum_percentiles_80 sum_percentiles_90]
    


           
% plot the bands 
        x=[1:length(time_serie_power_forecast(1,turbine_counter).data{2,7}(length(time_serie_power_forecast(1,turbine_counter).data{2,2})-(nr_data_points-1):length(time_serie_power_forecast(1,turbine_counter).data{2,2})))]

        for i=1:Namelist{5}.number_ci_plots % upper bands first 
            h(i)=ciplot(sum_percentiles(:,i+3),sum_percentiles(:,i+4),x,[0.2989 + 0.5870  + 0.1140],0.75/i)
            hold on
            h_lower(i)=ciplot(sum_percentiles(:,i+2),sum_percentiles(:,i+3),x,[0.2989 + 0.5870  + 0.1140],0.75/i)
            %hold on
        end
        hold on 
        
   %plot the deterministic forecast
        h_1=plot(sum_power,'--r*','LineWidth',2,...
                'MarkerEdgeColor','r',...
                'MarkerFaceColor','r',...   
                'MarkerSize',10)
    
            
            set(h(2),'LineStyle','none');set(h_lower(2),'LineStyle','none')
            set(h(1),'LineStyle','none');set(h_lower(1),'LineStyle','none')
            
            set(h(2),'Facealpha',0.6,'LineStyle','none');set(h_lower(2),'Facealpha',0.6,'LineStyle','none')
            set(h(1),'Facealpha',0.8,'LineStyle','none');set(h_lower(1),'Facealpha',0.8,'LineStyle','none')
            colormap('gray')

        legend([h_1,h(1)],{'Expected power','30-70 % percentiles'},'location','southeast','Box', 'off','fontsize',12)    
            
%            legend({,'Deterministic forecast','obs','50-60% percentile','40-50% percentile','60-70% percentile','30-40% percentile','70-80% percentile','20-30% percentile'})
            switch 1
                case strcmp(Namelist{2}.location{1},'LemKaer')
                    set(gca,'xlim',[0 nr_data_points],'ylim',[0 13000]); grid on; colormap('gray')
                case strcmp(Namelist{2}.location{1},'sprogoe')
                    set(gca,'xlim',[0 nr_data_points],'ylim',[0 21000]); grid on; colormap('gray')
            end
            
            % label stuff
            date_labels=power_obs_vector(1,turbine_counter).valid_date(:,11:16)
            set(gca,'xtick',[1:6:nr_data_points],'xticklabels',date_labels([1:6:(35/Namelist{5}.Analog.lead_delta)],:),'fontsize',Namelist{7}.fontsize_sub_plot-3)
            ylabel('Expected power in KW','fontsize',Namelist{7}.fontsize_sub_plot-3);
            xlabel(strcat('Valid for:',' ',[power_obs_vector(1,1).valid_date(1,1:5),' and ',datestr(addtodate(datenum(power_obs_vector(1,1).valid_date(1,1:10),'dd-mm-yyyy'),1,'day'),'dd-mm'),' Site:',Namelist{2}.location{1},' Init time:',last_updated(12:16)]),'fontsize',Namelist{7}.fontsize_sub_plot-3);
            try 
                if strcmp(computer('arch'),'win32') 
                    maximize 
                    if not(isdir(Namelist{1}.html_plots))
                        mkdir([Namelist{1}.html_plots])
                        save_file=[Namelist{1}.html_plots,'\power_forecast' Namelist{2}.location{1}]
                    else
                        save_file=[Namelist{1}.html_plots,'\power_forecast' Namelist{2}.location{1}]
                    end 
                    %print(gcf, '-dmeta', filename);
                    save_file_web=[Namelist{1}.html_department_2_plots,'\power_forecast_' Namelist{2}.location{1}]
                    %print(gcf, '-dmeta', filename);
                    print(gcf,'-djpeg',save_file_web)
                    %Save plots]
                    Succes='True';

                end

            catch
                display('Unable to maximize plot')
                 save_file_department=[Namelist{1}.html_plots '\power_forecast_' Namelist{2}.location{1}]
                 save_file_web=[Namelist{1}.html_department_2_plots,'\power_forecast_' Namelist{2}.location{1}]
                print(gcf,'-djpeg',save_file_web)
                
            end

            save_file_web=[Namelist{1}.html_department_2_plots,'\power_forecast_' Namelist{2}.location{1}]
            mkdir([save_file_web])
            print(gcf,'-djpeg',save_file_web)
         
            %Save plots]
            Succes='True';
