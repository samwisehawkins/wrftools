function [ data ] = get_time_series_ECMWFforecast(Namelist)
%UNTITLED Summary of this function goes here
%   Detailed explanation goes here
file_name=strcat(Namelist{1}.forecast_data_dir,Namelist{2}.location{1},'\determ_time_series')
fid = fopen(file_name)
    if fid==-1 
        (display(['The file:',file_name,' Was not found']))
    else
        fileInfo = dir(file_name);
        if not(isempty(fileInfo))
        fileSize = fileInfo.bytes; % make sure something is in the file 
        end
         format='%s%s%s%s%s%s%s%s%s%s%s%s'
         [headers]=textscan(fid,format,1,'HeaderLines',2); % to get whole data set remove 100 when done testing 
         format='%s%s%f%f%f%f%f%f%f%f%f%s'
         [data_tempo position]=textscan(fid,format); % to get whole data set remove 100 when done testing 
    end
    %Convert to standard date using wrf date format
    data{1,1}=datestr(datenum(data_tempo{1,1},'yyyymmddHH'),Namelist{1}.datstr_general_format);
    data{1,2}=datestr(datenum(data_tempo{1,2},'yyyymmddHH'),Namelist{1}.datstr_general_format);
    data{1,14}=int2str((datenum(data_tempo{1,2},'yyyymmddHH')-datenum(data_tempo{1,1},'yyyymmddHH'))*24)
    data{2,14}='Lead hour'
    
    %2m temperature
    data{1,3}=data_tempo{1,9}
    data{2,3}='Temperature 2 m'
    data{1,4}=data_tempo{1,10}
    data{2,4}='Temperature skin'
    
    data{1,5}=data_tempo{1,5}
    %wspd 10 m
    data{1,6}=((data_tempo{1,3}).^2+(data_tempo{1,4}).^2).^.5;
    data{2,6}='wind speed 10m'
    %Wdir 10 m
    data{1,7}=data_tempo{1,5};
    data{2,7}='Wind direction 10m';
    
    %mslp
    data{1,10}=data_tempo{1,11}
    data{2,10}='Mslp'
    
    data{1,27}=((data_tempo{1,7}).^2+(data_tempo{1,6}).^2).^.5;
    data{1,28}=data_tempo{1,8}
    
    data{2,27}='Wind speed 100m'
    data{2,28}='Wind direction 100m'
    
    data{2,1}=headers{1,1}
    data{2,2}=headers{1,2}
    
    fclose(fid);
        
        

