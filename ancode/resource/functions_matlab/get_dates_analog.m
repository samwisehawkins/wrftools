function [ dates_analog ] = get_dates_analog(Namelist,forecast_vector,data_set);
%GET_DATES_ANALOG Summary of this function goes here
%   Detailed explanation goes here
% function matches currant forecast vector with analogs from the past and
% returns the dates from when this state vector was last seen
%loop trough all lead times 
i=0;
delta_lead=Namelist{5}.Analog.lead_times(2)-Namelist{5}.Analog.lead_times(1);

for i=1:length(Namelist{5}.Analog.lead_times)
% so what goes on here ? We construct a reduced data set where only iniial
% prediction on the lead times are considered - this is not relevant when
% doing resource assesment
    
    time_serie_nwp_forecast_lead_idx=squeeze(int16(find(data_set.data(:,3)==Namelist{5}.Analog.lead_times(i))));
    time_serie_nwp_forecast_lead_idx_minus_1=int32(find(data_set.data(:,3)==Namelist{5}.Analog.lead_times(i)-(2*delta_lead)));
    time_serie_nwp_forecast_lead_idx_plus_1=find(find(data_set.data(:,3)==Namelist{5}.Analog.lead_times(i)+(2*delta_lead)));
    %only send variables to match on the right lead time
    %check() will print out the lead times on associated with i'te i step
    for j=1:length(Namelist{1,5}.Analog.state_vector_idx);
            
        Tempo_Historical_forecast_vector.var_data{1,j}=data_set.colheaders(:,Namelist{1,5}.Analog.state_vector_idx(j));
        Tempo_Historical_forecast_vector.var_data{3,j}=strcat(data_set.colheaders(Namelist{1,5}.Analog.state_vector_idx(j)),'lead t-1');
        Tempo_Historical_forecast_vector.var_data{5,j}=strcat(data_set.colheaders(Namelist{1,5}.Analog.state_vector_idx(j)),'lead t+1');
               
        Tempo_Historical_forecast_vector.var_data{2,j}=data_set.data(time_serie_nwp_forecast_lead_idx,Namelist{1,5}.Analog.state_vector_idx(j)); %put in the numbers on the right lead times 
        Tempo_Historical_forecast_vector.var_data{4,j}=data_set.data(time_serie_nwp_forecast_lead_idx_minus_1,Namelist{1,5}.Analog.state_vector_idx(j));
        Tempo_Historical_forecast_vector.var_data{6,j}=data_set.data(time_serie_nwp_forecast_lead_idx_plus_1,Namelist{1,5}.Analog.state_vector_idx(j));
        
    end
     
    % now match curent forecast vector on lead time with historical
    % forecast vector on lead time i
    
    switch 1
        case Namelist{10}.nwp_to_power_forecast_method==1 % parkvice
            [analogs.lead(i).predictands analog.lead(i).weights]=match_forecast_on_lead_time(Tempo_Historical_forecast_vector,forecast_vector,Namelist,i,data_set);
        case Namelist{10}.nwp_to_power_forecast_method==2  % turbine vice
            [analogs.lead(i).predictands analog.lead(i).weights]=match_forecast_on_lead_time_turbin_vice(Tempo_Historical_forecast_vector,forecast_vector,Namelist,i,data_set);
            %display(['lead:',num2str(i),' Hour'])
           
    end % switch 
            
            clear Tempo_Historical_forecast_vector    
    
end %for 
close all hidden
close all force
Namelist{5}.Analog.number_of_analogs_search_for;
end

