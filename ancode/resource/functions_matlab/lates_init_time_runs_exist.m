function [ is_there ] = lates_init_time_runs_exist(Namelist,lates_init_time) 
%UNTITLED Summary of this function goes here
%   Detailed explanation goes here
switch 1  
    case strcmp(Namelist{4}.nwp_model{1},'WRF')
                  ddtg=datestr(datenum(lates_init_time),'yyyymmddHH')
                  dir_name=['\TimeSeries_',datestr(datenum(lates_init_time),'yyyymmddHH'),'\']
                  domaine_group=['_','d0',num2str(Namelist{4}.nwp_model_domain),'_']
                  file_name=strcat(Namelist{1}.forcast_data_timerseries,dir_name,Namelist{2}.location{1},domaine_group,ddtg(1:length(ddtg)),'.dat')
                  fileInfo = dir(file_name);
            if not(isempty(fileInfo))
                fileSize = fileInfo.bytes; % make sure something is in the file 
                is_there=1;
            else
                is_there=0;
            end
end 

end

