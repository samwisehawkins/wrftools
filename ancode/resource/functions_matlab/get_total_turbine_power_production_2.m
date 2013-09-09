function [ total_turbine_power_production ] = get_total_turbine_power_production_2( Namelist,turbine_data )
%GET_TOTAL_PRODUCTION Summary of this function goes here
%   Sums the individual turbines power production for the the new data
%   observation format and fileds 
if Namelist{5}.use_clean_obs
    clean_idx=find(cellfun('length',turbine_data{1,2})==19);
    n_obs=datenum(cell2mat(turbine_data{1,2}(clean_idx)),'dd-mm-yyyy HH:MM:SS'); % ''yyyy-mm-dd HH:MM');
else
    n_obs=datenum(cell2mat(turbine_data{1,2}),Namelist{1}.datstr_turbine_input_format); % ''yyyy-mm-dd HH:MM');
end 
    disp(strcat('Observation started :',datestr(min(n_obs),Namelist{1}.datstr_turbine_input_format)));
    disp(strcat('Observation ended :',datestr(max(n_obs),Namelist{1}.datstr_turbine_input_format)));
    num_start_time=min(n_obs);
    num_current_time=num_start_time;
%disp(strcat('new obs time ',datestr(addtodate(num_start_time, 10, 'Minute'))));
% for all time between start date and end date, add 10 minutes and sum
% production if all turbiunes were running
dummy=1;
    total_turbine_power_production{2,1}= 'numer of observing turbine'
    total_turbine_power_production{2,2}='Time stamp'
    total_turbine_power_production{2,3}='Mean production kw'
    total_turbine_power_production{2,4}=' mean wind speed '
    total_turbine_power_production{2,5}='mean wind direction'  
    total_turbine_power_production{2,6}='numer of wind observing turbine'  
    disp(strcat('Observation started :',datestr(num_current_time,Namelist{1}.datstr_turbine_input_format)));
    
while addtodate(num_current_time, 1, 'Hour')<= max(n_obs)
    %while addtodate(num_current_time, 1, 'Hour')<= num_start_time+10
    %for testing works on only a small subset of obs
    %find all observation with same timestamp and all turbines in
    %functional operation accounting for mashine round off errors etc
    %datestr(num_current_time,Namelist{1}.datstr_turbine_input_format)
    indx=find(abs(num_current_time-n_obs)<1.1574e-005);
   % if the difference between n_obs and num_currant is less than 1 second we have a match
        
    if (isempty(indx)==0 & length(indx)==Namelist{1}.number_of_turbines_in_park) % Date match and all turbines are producing
        % check on missing values 
           [sorted_values, ia, ib] = setxor(turbine_data{1,3}(indx),['NULL']);
           % take only the power observation that are not NULL
           dummy_2=turbine_data{1,3}(indx);
           total_turbine_power_production{1,3}(dummy)=sum(dummy_2(ia));
           [sorted_values, ia, ib] = setxor(turbine_data{1,8}(indx),['NULL']);
           % take only the wspd observation that are not NULL
           dummy_2=turbine_data{1,8}(indx);
           total_turbine_power_production{1,4}(dummy)=mean(dummy_2(ia));
           % take only the wind-direction observation that are not NULL
           [sorted_values, ia, ib] = setxor(turbine_data{1,9}(indx),['NULL']);
           dummy_2=turbine_data{1,9}(indx);
           %dummy_2=cell2mat(cellfun(@str2num,turbine_data{1,9}(indx),'UniformOutput', false));
           total_turbine_power_production{1,5}(dummy)=mean(dummy_2);
           total_turbine_power_production{1,1}(dummy)=length(indx); % numer of observing turbine
           total_turbine_power_production{1,2}(dummy,:)=datestr(num_current_time,Namelist{1}.datstr_turbine_input_format);
           dummy=dummy+1;
           
    else % no match or only part of the park observing 
        switch 1
            case isempty(indx)
                % do nothing
            case Namelist{6}.Get_Power_Obs_even_when_not_all_is_producing==1 
                    total_turbine_power_production{1,1}(dummy)=length(indx); % numer of observing turbine
                    total_turbine_power_production{1,2}(dummy,:)=datestr(num_current_time,'yyyy-mm-dd HH:MM');
                    total_turbine_power_production{1,3}(dummy)=sum(turbine_data{1,3}(indx)); % Mean production kw
                    total_turbine_power_production{1,4}(dummy)=mean(turbine_data{1,8}(indx)); % mean wind speed 
                    total_turbine_power_production{1,5}(dummy)=mean(str2double(turbine_data{1,9}(indx))); % mean wind direction  
                    dummy=dummy+1;
    
        end% switch 
    end
    num_current_time=addtodate(num_current_time, 1, 'Hour');
    [Y, M, D, H, MN, S] = datevec(num_current_time);
    if MN~=0
           num_current_time=datenum(Y, M, D, H, 0, 0);
    end
    
    if mod(dummy,100)==0
    disp(strcat('operation on observation from :',datestr(num_current_time,Namelist{1}.datstr_general_format)));
    end 
  
    
end %while