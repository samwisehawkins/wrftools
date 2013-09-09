function data=get_time_series_ETAforecast_for_update(Namelist)
        fid = fopen(Namelist{1}.forecast_data_file_sprogoe_update)
        format='%u%s%s%f%f%f%f%f%f%f%f%f%f%f'
        [data_tempo position]=textscan(fid,format,'delimiter',','); % to get whole data set remove 100 when done testing 
        
switch 1
    case strcmp(Namelist{2}.location{1},'sprogoe')
        indx=find(data_tempo{1,1}==1) % find rows starting with 1 indicating sprogø
        %Namelist{1}.datstr_ETA_input_format='yyyy-mm-dd HH:MM:SS'
        % bring valid time to unified format
        data{1}= datestr(datenum(data_tempo{2}(indx),Namelist{1}.datstr_ETA_input_format),Namelist{1}.datstr_general_format)
        data{2}= datestr(datenum(data_tempo{3}(indx),Namelist{1}.datstr_ETA_input_format),Namelist{1}.datstr_general_format)
        data{3}= data_tempo{4}(indx)
        data{4}= data_tempo{5}(indx)
        data{5}= data_tempo{6}(indx)
        data{6}= data_tempo{7}(indx)
        data{7}= data_tempo{8}(indx)
        data{8}= data_tempo{9}(indx)
        data{9}= data_tempo{10}(indx)
        data{10}= data_tempo{11}(indx)
        data{11}= data_tempo{12}(indx)
        data{12}= data_tempo{13}(indx)
        data{13}= data_tempo{14}(indx)
        data{14}=get_lead_time( Namelist,data)
        
    case strcmp(Namelist{2}.location{1},'Lem_kjar')
        indx=find(data_tempo{1,1}==2)
        indx=find(data_tempo{1,1}==1) % find rows starting with 1 indicating sprogø
        data{1}= data_tempo{2}(indx)
        data{2}= data_tempo{3}(indx)
        data{3}= data_tempo{4}(indx)
        data{4}= data_tempo{5}(indx)
        data{5}= data_tempo{6}(indx)
        data{6}= data_tempo{7}(indx)
        data{7}= data_tempo{8}(indx)
        data{8}= data_tempo{9}(indx)
        data{9}= data_tempo{10}(indx)
        data{10}= data_tempo{11}(indx)
        data{11}= data_tempo{12}(indx)
        data{12}= data_tempo{13}(indx)
        data{13}= data_tempo{14}(indx)
        data{14}=get_lead_time( Namelist,data)
    case strcmp(Namelist{2}.location{1},'North_hoyle')
        indx=find(data_tempo{1,1}==3)
        indx=find(data_tempo{1,1}==1) % find rows starting with 1 indicating sprogø
        data{1}= data_tempo{2}(indx)
        data{2}= data_tempo{3}(indx)
        data{3}= data_tempo{4}(indx)
        data{4}= data_tempo{5}(indx)
        data{5}= data_tempo{6}(indx)
        data{6}= data_tempo{7}(indx)
        data{7}= data_tempo{8}(indx)
        data{8}= data_tempo{9}(indx)
        data{9}= data_tempo{10}(indx)
        data{10}= data_tempo{11}(indx)
        data{11}= data_tempo{12}(indx)
        data{12}= data_tempo{13}(indx)
        data{13}= data_tempo{14}(indx)
        data{14}=get_lead_time( Namelist,data);
end % switch
for i=1:length(data)
data{2,i}=Namelist{4}.ETA_forecast_fields{i}
end

