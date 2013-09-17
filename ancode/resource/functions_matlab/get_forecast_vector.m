function [ forecast_vector ] = get_forecast_vector(Namelist,data_set,num_init_times) ;
%GET_FORECAST Summary of this function goes here
%leadtime and state vextor diff are drivers here
%   Detailed explanation goes here
switch 1
    case strcmp(Namelist{4}.nwp_model{1},'WRF-Ris�')
        for i=1:length(Namelist{1,5}.Analog.state_vector_idx)
                forecast_vector.var_names{i}=data_set.colheaders{Namelist{1,5}.Analog.state_vector_idx(i)};
        end
    case strcmp(Namelist{4}.nwp_model{1},'ETA')
        forecast_vector.var_names=Namelist{4}.ETA_forecast_fields(Namelist{1,5}.Analog.state_vector_idx);
    case strcmp(Namelist{4}.nwp_model{1},'ECMWF')
        forecast_vector.var_names=Namelist{4}.ECMWF_forecast_fields(Namelist{1,5}.Analog.state_vector_idx);
end % switch 
[succes forecast_time_index]=get_forecast_index(Namelist,data_set,num_init_times);
% check if forecast is avaiable % unavaiable 28/10

while not(succes) % get next forecast available if current one does not exist 
    Namelist{5}.Analog.now=datestr(addtodate(datenum(Namelist{5}.Analog.now,Namelist{1}.datstr_turbine_input_format),1, 'day'),Namelist{1}.datstr_turbine_input_format);
    display(strcat('attempting forecasting from:',Namelist{5}.Analog.now));
    [succes forecast_time_index]=get_forecast_index(Namelist,data_set,num_init_times);
end

for i=1:length(Namelist{1,5}.Analog.state_vector_idx)
    switch 1
        case strcmp(Namelist{4}.nwp_model{1},'WRF-Ris�')
            forecast_vector.var_data{1}=forecast_vector.var_names;
            forecast_vector.var_data{2,i}=data_set.data(forecast_time_index,Namelist{1,5}.Analog.state_vector_idx(i));
          % resource assesment is without lead times please reconcider code from here ;)
            % the data is ordered so forecast_time_index+1 is valid time +
            % 1 hour 
            % and forecast_time_index-1 is valid time -1 hour _lead time is obsolite here 
            % fix that lead time is always 0 confusing
            forecast_vector.var_data{3,i}=strcat(forecast_vector.var_names{1,i},'lead t-1');
            forecast_vector.var_data{4,i}=data_set.data(forecast_time_index-1,Namelist{1,5}.Analog.state_vector_idx(i));   
            forecast_vector.var_data{5,i}=strcat(forecast_vector.var_names{1,i},'lead t+1');
            forecast_vector.var_data{6,i}=data_set.data(forecast_time_index+1,Namelist{1,5}.Analog.state_vector_idx(i));   
            forecast_vector.var_data{7,i}='Valid time';
            forecast_vector.var_data{8,i}=num2str(data_set.data(forecast_time_index+1,1));   
    
            
        case strcmp(Namelist{4}.nwp_model{1},'ETA')
            tempo=Namelist{4}.ETA_forecast_fields(Namelist{1,5}.Analog.state_vector_idx);
            forecast_vector.var_data{1,i}=tempo{1,i};
            forecast_vector.var_data{2,i}=data_set{1,Namelist{1,5}.Analog.state_vector_idx(i)}(forecast_time_index,:);
            forecast_vector.var_data{3,i}=strcat(tempo{1,i},'lead t-1');
            forecast_vector.var_data{4,i}=data_set{1,Namelist{1,5}.Analog.state_vector_idx(i)}(forecast_time_index-1,:);
            forecast_vector.var_data{5,i}=strcat(tempo{1,i},'lead t+1');
            forecast_vector.var_data{6,i}=data_set{1,Namelist{1,5}.Analog.state_vector_idx(i)}(forecast_time_index+1,:);
    
        case strcmp(Namelist{4}.nwp_model{1},'ECMWF')
            tempo=Namelist{4}.ECMWF_forecast_fields(Namelist{1,5}.Analog.state_vector_idx);
            forecast_vector.var_data{1,i}=tempo{1,i};
            forecast_vector.var_data{2,i}=data_set{1,Namelist{1,5}.Analog.state_vector_idx(i)}(forecast_time_index,:);
            forecast_vector.var_data{3,i}=strcat(tempo{1,i},'lead t-1');
            forecast_vector.var_data{4,i}=data_set{1,Namelist{1,5}.Analog.state_vector_idx(i)}(forecast_time_index-1,:);
            forecast_vector.var_data{5,i}=strcat(tempo{1,i},'lead t+1');
            forecast_vector.var_data{6,i}=data_set{1,Namelist{1,5}.Analog.state_vector_idx(i)}(forecast_time_index+1,:);
    
    end
    
    
end

