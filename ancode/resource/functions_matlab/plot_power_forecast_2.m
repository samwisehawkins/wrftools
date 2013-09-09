function [ Succes ] = plot_power_forecast_2(time_serie_power_forecast,power_obs_vector,Namelist)
%PLOT_POWER_FORECAST Summary of this function goes here
%   Detailed explanation goes here
close all
 % plot deterministic 
        plot(time_serie_power_forecast{2,7}(length(time_serie_power_forecast{2,2})-24:length(time_serie_power_forecast{2,2}))/Namelist{10}.name_plate_capasity_kw,'--r*','LineWidth',2,...
                'MarkerEdgeColor','r',...
                'MarkerFaceColor','r',...
                'MarkerSize',10)
        hold on 
        % plot obs
            plot(power_obs_vector.corrected_obs_vector.power_obs/Namelist{10}.name_plate_capasity_kw,'--k*','LineWidth',2,...
                'MarkerEdgeColor','b',...
                'MarkerFaceColor','k',...
                'MarkerSize',10)
    %legend({'Deterministic forecast','obs'})
            
        if Namelist{10}.normalize_errors
            for i=[3 4 5 6 8 9 10 11] % 4 outerpercentiles 
        %    plot(time_serie_power_forecast{2,i}(:)/Namelist{10}.name_plate_capasity_kw,'--r')
            hold on
            end
        else
            plot(time_serie_power_forecast{2,2}(length(time_serie_power_forecast{2,2})-24:length(time_serie_power_forecast{2,2})))
        end
        % plot the bands 
        x=[1:length(time_serie_power_forecast{2,7}(length(time_serie_power_forecast{2,2})-24:length(time_serie_power_forecast{2,2})))]
        for i=1:Namelist{5}.number_ci_plots % upper bands first 
            h(i)=ciplot(time_serie_power_forecast{2,7+i-1}(length(time_serie_power_forecast{2,2})-24:length(time_serie_power_forecast{2,2}))/Namelist{10}.name_plate_capasity_kw,time_serie_power_forecast{2,7+i}(length(time_serie_power_forecast{2,2})-24:length(time_serie_power_forecast{2,2}))/Namelist{10}.name_plate_capasity_kw,x,[0.2989 + 0.5870  + 0.1140],0.75/i)
            hold on
            h_lower(i)=ciplot(time_serie_power_forecast{2,7-i+1}(length(time_serie_power_forecast{2,2})-24:length(time_serie_power_forecast{2,2}))/Namelist{10}.name_plate_capasity_kw,time_serie_power_forecast{2,7-i}(length(time_serie_power_forecast{2,2})-24:length(time_serie_power_forecast{2,2}))/Namelist{10}.name_plate_capasity_kw,x,[0.2989 + 0.5870  + 0.1140],0.75/i)
            %hold on
        end
            
            set(h(3),'LineStyle','none');set(h_lower(3),'LineStyle','none')
            set(h(2),'LineStyle','none');set(h_lower(2),'LineStyle','none')
            set(h(1),'LineStyle','none');set(h_lower(1),'LineStyle','none')
            
            set(h(3),'Facealpha',0.4,'LineStyle','none');set(h_lower(3),'Facealpha',0.4,'LineStyle','none')
            set(h(2),'Facealpha',0.6,'LineStyle','none');set(h_lower(2),'Facealpha',0.6,'LineStyle','none')
            set(h(1),'Facealpha',0.8,'LineStyle','none');set(h_lower(1),'Facealpha',0.8,'LineStyle','none')
            colormap('gray')

            legend({,'Deterministic forecast','obs','50-60% percentile','40-50% percentile','60-70% percentile','30-40% percentile','70-80% percentile','20-30% percentile'})
            set(gca,'xlim',[0 25],'ylim',[0 1]); grid on; colormap('gray')
            % label stuff
            date_labels=power_obs_vector.valid_date(:,11:16)
            set(gca,'xtick',[1:3:25],'xticklabels',date_labels([1:3:24],:),'fontsize',Namelist{7}.fontsize)
            title('Flow dependent percentiles from Analog Ensemble approch','fontsize',Namelist{7}.fontsize)
            ylabel('Normalized power (nameplate capacity)','fontsize',Namelist{7}.fontsize);
            xlabel(strcat('Valid for:',' ',power_obs_vector.valid_date(1,1:10)),'fontsize',Namelist{7}.fontsize);
            maximize
            %Save plots 
            filename=strcat([Namelist{1}.plots_forecast_dir],'Pro_forecast_valid_',power_obs_vector.valid_date(1,1:10));
            mkdir(Namelist{1}.plots_forecast_dir);
            print(gcf, '-dmeta', filename);
            print(gcf, '-dpng', filename);
            
            Succes='True';
end







