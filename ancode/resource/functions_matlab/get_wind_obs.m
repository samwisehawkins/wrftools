function [ wind_obs] = get_wind_obs(data_set,Namelist,n_now,num_valid_date)
                       
obs_idx=find(abs(num_valid_date-n_now)<1.1574e-005);
wind_obs=data_set.data(obs_idx,26);%
end

