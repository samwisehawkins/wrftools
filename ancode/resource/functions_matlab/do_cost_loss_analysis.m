function [ succes ] = do_cost_loss_analysis( Namelist )
%DO_TURBINE_BY_TURBINE_STAT Summary of this function goes here
%   Detailed explanation goes here
use_fixed_tresshold=1
fixed_tresshold=0.5
close all
            data_dir=[Namelist{1}.workspace_data_dir,'\experiments\',Namelist{11}.experiment,'\']
            load([data_dir,'turbine_time_series_for_nr_analogs_',num2str(8)])
            
            [m n]=size(turbine_time_series)
            
 % choose turbine for investigation 
 
 turbine_nr=2;
 nr_obs=length(turbine_time_series(1,turbine_nr).data{2,15})
 nr_good_obs=length(find(turbine_time_series(1,turbine_nr).data{2,15}~=Namelist{1}.missing_value));
 norm_power_fct=turbine_time_series(1,turbine_nr).data{2,13}/Namelist{10}.rated_capasity_kw;
 norm_power_fct_distrib=turbine_time_series(1,turbine_nr).data{2,18}/Namelist{10}.rated_capasity_kw;
 norm_power_obs=turbine_time_series(1,turbine_nr).data{2,15}/Namelist{10}.rated_capasity_kw;
 
 % normalize all power data 
 a=0 ; %event forecast and occur
 b=0 ; % event forecasted but dit not occur
 c=0;  %event not forecast but did occur
 d=0;  % event not forecast and did not occur all is good very good
 p_a=0;p_b=0;p_c=0;p_d=0;
first_time=1
counter=0
 event_tresshold=0.95 % turbine producing more than 50%
 treshold_counter=0
 %loop over cost_loss_ratio
cost_los_vector=[0.01:0.01:1]
for fixed_tresshold=[0.15:0.05:0.45]
    treshold_counter=treshold_counter+1
 for cost_loss_ratio=cost_los_vector
     
     counter=counter+1;
     for i=1:nr_obs
       % deterministic part 
         switch 1
             case norm_power_fct(i)>event_tresshold % forecast størrere end event_tresshold
                 % update right number according to observation
                 if (turbine_time_series(1,turbine_nr).data{2,15}(i)~=Namelist{1}.missing_value)&norm_power_obs(i)>event_tresshold;
                     % event forecasted and took place 
                     a=a+1;
                 else
                     b=b+1;
                 end
             case norm_power_fct(i)<event_tresshold & norm_power_obs(i)>event_tresshold % not forecasted but did take place
                 % update right number according to observation
                 if (turbine_time_series(1,turbine_nr).data{2,15}(i)~=Namelist{1}.missing_value)&norm_power_obs(i)>event_tresshold;
                     % event not forecasted but took place 
                     c=c+1;
                 end
             case norm_power_fct(i)<event_tresshold & norm_power_obs(i)<event_tresshold  % not forecasted and did nok take place 
                 d=d+1; % all is good, very good
         end
   
     
    %probabilistic part 
    if use_fixed_tresshold==1
        desision_treshold_power=prctile(norm_power_fct_distrib(i,:),(100-(fixed_tresshold)*100));
    else
        desision_treshold_power=prctile(norm_power_fct_distrib(i,:),(100-(cost_loss_ratio)*100));
    end
    
    %cdfplot(turbine_time_series(1,turbine_nr).data{2,18}(i,:))
      switch 1
             case desision_treshold_power>event_tresshold % forecast størrere end event_tresshold
                 % update right number according to observation
                 if (turbine_time_series(1,turbine_nr).data{2,15}(i)~=Namelist{1}.missing_value)&norm_power_obs(i)>event_tresshold;
                     % event forecasted and took place 
                     p_a=p_a+1;
                 else
                     p_b=p_b+1;
                 end
             case desision_treshold_power<event_tresshold & norm_power_obs(i)>event_tresshold
                 % update right number according to observation
                 if (turbine_time_series(1,turbine_nr).data{2,15}(i)~=Namelist{1}.missing_value);
                     % event not forecasted but took place 
                     
                     p_c=p_c+1;
                 end
        case desision_treshold_power<event_tresshold & norm_power_obs(i)<event_tresshold;%  % forecast mindre end event_tresshold 
                if (turbine_time_series(1,turbine_nr).data{2,15}(i)~=Namelist{1}.missing_value)
                    p_d=p_d+1;
                end
         end
     end % obs loops 
     
     p.determ.a=a/nr_good_obs;
     p.determ.b=b/nr_good_obs;
     p.determ.c=c/nr_good_obs;
     p.determ.d=d/nr_good_obs;
     p.determ.Hit_rate(counter)=(p.determ.a)/(p.determ.a+p.determ.c);
     p.determ.False_alarm_rate(counter)=p.determ.b/(p.determ.b+p.determ.d);
     if first_time
        p.delta=length(find(norm_power_obs>event_tresshold))/nr_good_obs;
     end
     p.C_L_ratio(counter)=cost_loss_ratio;
     value_term_1=min([p.delta,cost_loss_ratio]);
     value_term_2=p.determ.False_alarm_rate(counter)*(1-p.delta)*cost_loss_ratio;
     value_term_3=p.determ.Hit_rate(counter)*p.delta*(1-cost_loss_ratio);
     value_term_4=p.delta;
     value_term_5=p.delta*cost_loss_ratio;
     p.determ.forecast_prob_value(counter)=(value_term_1-value_term_2+value_term_3-value_term_4)/(value_term_1-value_term_5);
     clear value_term_1 value_term_2 value_term_3 value_term_4 value_term_5
     
     
     p.prob.a(counter)=p_a/nr_good_obs;
     p.prob.b(counter)=p_b/nr_good_obs;
     p.prob.c(counter)=p_c/nr_good_obs;
     p.prob.d(counter)=p_d/nr_good_obs;
     p.prob.Hit_rate(counter)=(p_a)/(p_a+p_c);
     p.prob.False_alarm_rate(counter)=p_b/(p_b+p_d);
     if first_time
        p.delta=length(find(norm_power_obs>event_tresshold))/nr_good_obs;
     end
     p.C_L_ratio(counter)=cost_loss_ratio;
     value_term_1=min([p.delta,cost_loss_ratio]);
     value_term_2=p.prob.False_alarm_rate(counter)*(1-p.delta)*cost_loss_ratio;
     value_term_3=p.prob.Hit_rate(counter)*p.delta*(1-cost_loss_ratio);
     value_term_4=p.delta;
     value_term_5=p.delta*cost_loss_ratio;
     p.prob.forecast_prob_value(counter)=(value_term_1-value_term_2+value_term_3-value_term_4)/(value_term_1-value_term_5)
     p.prob.forecast_prob_value_fixed_treshold(counter,treshold_counter)=(value_term_1-value_term_2+value_term_3-value_term_4)/(value_term_1-value_term_5)
     p.prob.trehold(treshold_counter)=fixed_tresshold
     p_a=0;p_b=0;p_c=0;p_d=0;% remember to initialize p_counters :)
     a=0 ; %event forecast and occur
     b=0 ; % event forecasted but dit not occur
     c=0;  %event not forecast but did occur
     d=0;  % event not forecast and did not occur all is good very good
     first_time=0;     
    %    
 end % cost loss ratio loop 
counter=0
end %(fix_trehold loop)

 color_1=rgb('DarkGrey')
 color_2=rgb('LightGrey')
 
 plot_h_1=plot(p.prob.forecast_prob_value);hold on
 set(plot_h_1,'Color',color_1,'LineWidth',6)
 plot_h_2=plot(p.determ.forecast_prob_value,':');
 set(plot_h_2,'Color','black','LineWidth',6)
 
 ylabel('Value','fontsize',Namelist{7}.fontsize);xlabel('Cost/Loss','fontsize',Namelist{7}.fontsize)
 legend('Probabilistic','Deterministic')
 
 set(gca,'ylim',[0 0.45],'xlim',[0 60],'xtick',[1:10:length(cost_los_vector)],'xticklabels',cost_los_vector(1:10:length(cost_los_vector))...
 ,'fontsize',Namelist{7}.fontsize);title(['Value of forecasting power production more than 80% with observed delta=', sprintf('%0.2g',p.delta)],'fontsize',Namelist{7}.fontsize)
 set(gca,'ytick',[0:0.05:1]);
 grid on;maximize           
 
 figure
 [m n]=size(p.prob.forecast_prob_value_fixed_treshold)
     for i=1:n
         plot_h_1=plot(p.prob.forecast_prob_value_fixed_treshold(:,i),[':',Namelist{5}.markers(i)],'MarkerSize',10);hold on
         color_1=rgb(cell2mat(Namelist{5}.color(i)))
         set(plot_h_1,'Color',color_1,'LineWidth',3)
         legendstr{i}=strcat('Tresshold:',sprintf('%0.2g',p.prob.trehold(i)))
     end
        legendstr{i+1}='Deterministic'
        plot_h_2=plot(p.determ.forecast_prob_value,':');
        set(plot_h_2,'Color','black','LineWidth',3)
 
 ylabel('Value','fontsize',Namelist{7}.fontsize);xlabel('Cost/Loss','fontsize',Namelist{7}.fontsize)
 legend(legendstr)
 set(gca,'ylim',[0 0.5],'xlim',[0 60],'xtick',[1:10:length(cost_los_vector)],'xticklabels',cost_los_vector(1:10:length(cost_los_vector))...
 ,'fontsize',Namelist{7}.fontsize);title(['Value of forecasting power production more than 95% with observed delta=', sprintf('%0.2g',p.delta)],'fontsize',Namelist{7}.fontsize)
 set(gca,'ytick',[0:0.05:1]);
 grid on;maximize           
        
 figure
 mtx(1,:)=[p.determ.False_alarm_rate(1) p.prob.False_alarm_rate(1)]
 mtx(2,:)=[p.determ.Hit_rate(1) p.prob.Hit_rate(1)]
 
 bar(mtx','grouped');legend({'Deterministic','probabilistic'});
 set(gca,'xticklabels',{'False alarm rate','Hit rate'},'fontsize',Namelist{7}.fontsize);grid on;colormap('gray');
 
 
succes='true'
end

