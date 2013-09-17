function [turbine_time_series]=add_eps_time_series(Namelist,turbine_time_series)
 eps_fili=[Namelist{1}.ecmwf_eps_dir_in,'/eps_sprogoe_time_series_and_power_obs.txt']
 fid = fopen(eps_fili);
textscan(fid, '%c', 3);
 [data] = textscan(fid, '%s%s%f%f%u%u%f%f%f%f%f%f%f%f','Headerlines',4);
 headers={'Init','Valid' 'Ecmwf_U_wind' 'Ecmwf_V_wind' 'Ensemble_member' 'Lead_hour' 'Predicted_power' 'obs_power_turbine_1'...
           'obs_power_turbine_2' 'obs_power_turbine_3' 'obs_power_turbine_4' ...
           'obs_power_turbine_5' 'obs_powe_turbine_6' 'obs_power_turbine_7'}
[m n]=size(turbine_time_series)
ecmwf_dates=datenum(data{2},'yyyymmddHH');
done=0
% Leadtime loop
while not(done) 
    for i=1:n
        turb_date=datenum(turbine_time_series(1,i).data{2,1},Namelist{1}.datstr_general_format);
        obs_length=length(turb_date)
        %find verifing date
        for j=1:obs_length
            lead=mod(j,24)+11
            idx=find(turb_date(j)==ecmwf_dates)
            match_idx=idx(find(lead==data{1,6}(idx)))  
            if not(isempty(match_idx))
                turbine_time_series(1,i).data{2,20}(j,:)=data{1,7}(match_idx);
                turbine_time_series(1,i).data{1,20}='power from ECMWF';
                turbine_time_series(1,i).data{2,21}(j,:,:)=char(data{1,2}(match_idx));
            end
        end
    end
    if (j==obs_length)&(i==n)
        done=1
    end
end %while
fclose(fid)
    
end

