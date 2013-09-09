function [ lead_time ] = get_lead_time( Namelist,time_serie_nwp_forecast)
%GET_LEAD_TIME Summary of this function goes here
%   Detailed explanation goes here
% here convert valid date to num
n_init=datenum((time_serie_nwp_forecast{1,1}),Namelist{1}.datstr_general_format);
n_valid=datenum((time_serie_nwp_forecast{1,2}),Namelist{1}.datstr_general_format);

[Y_first, M_first, D_first, H_first, MN_first, S_first] = datevec(n_valid(1));
[Y_next, M_next, D_next, H_next, MN_next, S_next] = datevec(n_valid(2));
    data_dump_frequency=H_next-H_first
    lead=0
    for i=1:length(n_init)-1
        if n_init(i)==n_init(i+1)
            lead_time(i,:)=sprintf('%02u',lead);
            lead=lead+1
        else
            lead_time(i,:)=sprintf('%02u',lead);
            lead_max=lead;
            lead=0
        end % if
       
    end 
    lead_time(length(n_init),:)=sprintf('%02u',lead_max);;
end

