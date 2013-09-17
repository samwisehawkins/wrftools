function [  sub_setted_data_set] = sub_set_data_set(Namelist,data_set,num_valid_date)
%UNTITLED2 Summary of this function goes here
%   Detailed explanation goes here
    train_start=datenum(num2str(Namelist{5}.start_analog_search_period),'yyyymmddHH');
    train_end=datenum(num2str(Namelist{5}.end_analog_search_period),'yyyymmddHH');
    start_idx=find(abs(num_valid_date-train_start)<.01)
    end_idx=find(abs(num_valid_date-train_end)<.01)
    sub_setted_data_set.data=data_set.data(start_idx:end_idx,:);
    sub_setted_data_set.colheaders=data_set.colheaders;
    sub_setted_data_set.textdata=data_set.textdata;
end
