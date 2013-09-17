function [ num_init_dates ] = get_num_init_dates(data_set)
%UNTITLED2 Summary of this function goes here
%   Detailed explanation goes here

for i=1:length(data_set.data(:,2))
    try
        num_init_dates(i)=datenum(num2str(data_set.data(i,2)),'yyyymmddHHMM');
    catch
        num_init_dates(i)=-999;
    end
end 
%UNTITLED Summary of this function goes here
%   Detailed explanation goes here

end

