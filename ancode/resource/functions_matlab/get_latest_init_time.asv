function [ out ] =get_latest_init_time(Y, M, D, H, MN, S,Namelist) 
%UNTITLED Summary of this function goes here
%   Detailed explanation goes here
      [val idx]=min(abs(H-Namelist{1}.forecast_initial_time));
               switch 1 % currently only two options but could be more with more initial times 
                   case (H-Namelist{1}.forecast_initial_time(idx))<0 %initial time later then now
                       init_time=Namelist{1}.forecast_initial_time(idx-1);
                   case (H-Namelist{1}.forecast_initial_time(idx))>=0
                       init_time=Namelist{1}.forecast_initial_time(idx);
               end
               display(['closest available run initilized at: ', datestr([Y M D init_time 0 0],'yyyy-mm-dd HH:MM')])
        out=datestr([Y M D init_time 0 0],'yyyy-mm-dd HH:MM')

end

