function [ winds weights ] = match_forecast_Resorce_assesment(forecast_vector,Namelist,data_set)
%MATCH_FORECAST_ON_LEAD_TIME Summary of this function goes here
%   Detailed explanation goes here

% first compute all distances


    distance=get_distance(forecast_vector,Namelist,data_set);
    % now sort all the distances from initial prediction obs pair 2 until lenght -1 and grab the best analogs  
    [analog_dis analog_idx]=sort(distance);
    analog_idx=analog_idx+2;
   % analog_idx=analog_idx-1;
    winds=data_set.data(analog_idx(1:Namelist{5}.Analog.number_of_analogs_search_for),26);
    norm_factor=1./analog_dis(1:Namelist{5}.Analog.number_of_analogs_search_for);
    analog_dates=num2str(data_set.data(analog_idx(1:Namelist{5}.Analog.number_of_analogs_search_for),1));

    for i=1:Namelist{5}.Analog.number_of_analogs_search_for
        weights(i)=((1/analog_dis(i)))/sum(norm_factor);
    end
    
 % check the results
 %analogmtx(1,:)=,2}(analog_idx(1:Namelist{5}.Analog.number_of_analogs_search_for)); %wspd
 analogmtx(2,:)=data_set.data(analog_idx(1:Namelist{5}.Analog.number_of_analogs_search_for),5); % wind speed 
 alogmtx(3,:)=data_set.data(analog_idx(1:Namelist{5}.Analog.number_of_analogs_search_for),25); % bulk richardson
 analogmtx(4,:)=data_set.data(analog_idx(1:Namelist{5}.Analog.number_of_analogs_search_for),24); %wind direction
 
 if Namelist{7}.analog_plot
     subplot(4,1,1)
     hist(analogmtx(1,:));legend(strcat('True:',num2str(forecast_vector.var_data{2,2}),' m/s'));grid on;
     subplot(4,1,2)
     hist(analogmtx(2,:));legend(strcat('True:',num2str(forecast_vector.var_data{2,3}),' Degree north'));grid on;
     subplot(4,1,3)
     hist(analogmtx(3,:));legend(strcat('True:',num2str(forecast_vector.var_data{2,4}),' hpa'));grid on;
     subplot(4,1,4)
     hist(analogmtx(4,:));legend(strcat('True:',num2str(forecast_vector.var_data{2,5}),' kg/m3'));grid on;
     filename=strcat(Namelist{1}.plots_data_dir,'Analog_ditribution on lead_',num2str(leadtime),Namelist{5}.Analog.now)
     print('-djpeg',filename)

 end % if 
 
 
 




end

