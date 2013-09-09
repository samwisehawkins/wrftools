function [ succes ] =plot_distributions( Namelist,savefile )
%UNTITLED Summary of this function goes here
% plots to test the downscaling techniques in getting the distributions correct    
load(savefile)

% simpe time series 
switch 1
    case 0
       plot(time_serie_winds{2,2},'b');hold on
       plot(time_serie_winds{2,21},'r'); hold on
       plot(time_serie_winds{2,20},'g');legend({'analog predictions','observations','raw nwp prediction'});grid on

 % distribution plot
    case 1
         [f,xi]=ksdensity(time_serie_winds{2,2})
            plot(xi,f,'b')
         [f,xi]=ksdensity(time_serie_winds{2,21})
            hold on
            plot(xi,f,'r')
         [f,xi]=ksdensity(time_serie_winds{2,20})
            hold on
         plot(xi,f,'g')
         legend({'analog predictions','observations','raw nwp prediction'});grid on
end % switch
 
   
end

