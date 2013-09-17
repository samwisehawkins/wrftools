function [ output_args ] = plot_rank(rank,Namelist,model,domaine,exp_name,analogs,type);
%PLOT_RANK Summary of this function goes here
%   Detailed explanation goes here
figure;frquency_yaxis=1
if frquency_yaxis
    freq_rank=rank/sum(rank);bar(freq_rank);set(gca,'ylim',[0 0.5]);ylabel('Freq','fontsize',15)
else
    bar(rank);ylabel('Count','fontsize',15)
end
    
xlabel('Analogs','fontsize',15);;set(gca,'fontsize',15)
grid on; colormap('gray')
title_str=['Model=',model,' Domaine=',num2str(domaine),' Nr analogs=',num2str(analogs),' Ranking type=',type]
title(title_str,'fontsize',15)

           save_dir=[Namelist{1}.stat_plot_dir,'\prob-plots\rank_histograms\']
            plot_filename=[model,'_Anlogs_',num2str(analogs),'_type-',type,'_d_',num2str(domaine)]
                    if isdir(save_dir)
                       saveas(gcf,[save_dir plot_filename] ,'fig')
                       saveas(gcf,[save_dir plot_filename] ,'jpeg')

                    else
                        mkdir(save_dir)
                        saveas(gcf,[save_dir plot_filename] ,'fig')
                        saveas(gcf,[save_dir plot_filename] ,'jpeg')

                    end

end

