function [ data_set] = load_data( Namelist )
%LOAD_DATA Summary of this function goes here
%   Read in the ETA or wrf nwp forecast 
%   Reads in the turbine observbations 
fili=strcat(Namelist{1}.obs_dir,Namelist{1}.obs_filename)
 data_set= importdata(fili, ' ', 1);
end % function 



