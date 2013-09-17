function [ turbine ] = parse_obs_turbine_by_turbine( Namelist,turbine_data )

[m n]=size(turbine_data)
for turbinecounter=1:n
    dates=turbine_data(1,turbinecounter).time_local;
    if Namelist{5}.use_clean_obs
        clean_idx=find(cellfun('length',dates)==19);
        n_obs=datenum(cell2mat(dates(clean_idx)),'dd-mm-yyyy HH:MM:SS'); % ''yyyy-mm-dd HH:MM');
    else
        n_obs=datenum(cell2mat(dates),Namelist{1}.datstr_turbine_input_format); % ''yyyy-mm-dd HH:MM');
    end 
    disp(strcat('Observation started :',datestr(min(n_obs),Namelist{1}.datstr_turbine_input_format)));
    disp(strcat('Observation ended :',datestr(max(n_obs),Namelist{1}.datstr_turbine_input_format)));
    num_start_time=min(n_obs);
    num_current_time=num_start_time;

    turbine(turbinecounter).power_production{1,1}=cell2mat(turbine_data(1,turbinecounter).unitid(1))
    turbine(turbinecounter).power_production{2,1}='Turbine id'
    turbine(turbinecounter).power_production{2,2}='Time stamp'
    turbine(turbinecounter).power_production{2,3}='Mean production kw'
    turbine(turbinecounter).power_production{2,4}='mean wind speed '
    turbine(turbinecounter).power_production{2,5}='mean wind direction'  
   
    turbine(turbinecounter).power_production{1,2}=turbine_data(1,turbinecounter).time_local(clean_idx,:);
    turbine(turbinecounter).power_production{1,3}=cellfun(@str2num,strrep(turbine_data(1,turbinecounter).actual_avg_power(clean_idx), ',', '.'));
    turbine(turbinecounter).power_production{1,4}=cellfun(@str2num,strrep(turbine_data(1,turbinecounter).wspd(clean_idx), ',', '.'));
    turbine(turbinecounter).power_production{1,5}=cellfun(@str2num,strrep(turbine_data(1,turbinecounter).wdir(clean_idx), ',', '.'));
    % now assign all observations 
    dates=turbine_data(1,turbinecounter).all_time_local;
    if Namelist{5}.use_clean_obs
        clean_idx=find(cellfun('length',dates)==19);
        n_obs=datenum(cell2mat(dates(clean_idx)),'dd-mm-yyyy HH:MM:SS'); % ''yyyy-mm-dd HH:MM');
    else
        n_obs=datenum(cell2mat(dates),Namelist{1}.datstr_turbine_input_format); % ''yyyy-mm-dd HH:MM');
    end 
    
    turbine(turbinecounter).wind_all{1,2}=turbine_data(1,turbinecounter).all_time_local(clean_idx,:);
    turbine(turbinecounter).wind_all{1,4}=cellfun(@str2num,strrep(turbine_data(1,turbinecounter).all_wspd(clean_idx), ',', '.'));
    turbine(turbinecounter).wind_all{1,5}=cellfun(@str2num,strrep(turbine_data(1,turbinecounter).all_wdir(clean_idx), ',', '.'));
    
    turbine(turbinecounter).wind_all{2,2}='Time stamp'
    turbine(turbinecounter).wind_all{2,3}='Mean production kw'
    turbine(turbinecounter).wind_all{2,4}='mean wind speed '
    turbine(turbinecounter).wind_all{2,5}='mean wind direction'  
        
    
end % for turbine counter 