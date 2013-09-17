function [ power_curve ] = get_power_curve( Namelist )
%GET_POWER_CURVE Summary of this function goes here
%   Det
    fid=fopen(Namelist{1}.power_curve_file);
    InputText=textscan(fid,'%s',3,'delimiter','\n'); % read 3 header line 
    % holds infor about the data fields
    dummy= regexp(InputText{1,1}{1,1}, '\s', 'split');
    for i=3:length(dummy)-1
        density_headers(i-2)=str2num(dummy{1,i});
    end 
    format='%d %d %d %d %d %d %d %d %d %d %d %d %d';
    [data position]=textscan(fid,format,'delimiter',' ');
    power_curve{2,1}='Density';
    power_curve{2,2}='Windspeed';
    power_curve{2,3}='Power';
    power_curve{1,1}=density_headers;
    power_curve{1,2}=data{1,1}';
    
    for i=2:length(data)
         power_curve{1,3}{i-1}=data{1,i};
        
    end
    %remove wind speeds 
    fclose('all');
end

