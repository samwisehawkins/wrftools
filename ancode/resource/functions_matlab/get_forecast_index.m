function [succes forecast_time_idx] =get_forecast_index(Namelist,data_set,num_init_times)
% Summary of this function goes here
%   Detailed explanation goes here
now=datenum(Namelist{5}.Analog.now,Namelist{1}.datstr_turbine_input_format);
% take all forecast with initial date = now
%num_init_times=datenum(int2str(data_set.data(:,1)),Namelist{1,1}.datstr_general_format);
forecast_time_all_idx=find(abs(now-num_init_times)<1.1574e-005);%Indenfor et sekund af initial tid

    if isempty(forecast_time_all_idx)
        forecast_time_all_idx=0;
        succes=0;
        forecast_time_idx=Namelist{1}.missing_value;
    else
        for i=1:length(Namelist{5}.Analog.lead_times)
            %make check on that lead time does only occour once
            dummy=find(Namelist{5}.Analog.lead_times(i)==data_set.data(forecast_time_all_idx,3));
            if length(dummy)>1
                lead_idx(i)=dummy(1);
            else 
                lead_idx(i)=dummy;
            end 
        end
        forecast_time_idx=forecast_time_all_idx(lead_idx);
        succes=1;
    end
%data_set{1,2}(forecast_time_idx,:)
end

