function [ num_valid_dates] =get_num_valid_dates(data_set) 
% simple function to check for missing values 
for i=1:length(data_set.data(:,1))
    try
        num_valid_dates(i)=datenum(num2str(data_set.data(i,1)),'yyyymmddHHMM');
    catch
        num_valid_dates(i)=-999;
    end
end 
%UNTITLED Summary of this function goes here
%   Detailed explanation goes here


end

