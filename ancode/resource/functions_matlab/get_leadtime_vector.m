function [ leadtime_vector ] = get_leadtime_vector(turbine_time_series,Namelist)
%GET_LEADTIME_VECTOR Summary of this function goes here
%   Detailed explanation goes here
Namelist_Analog_lead_times_counter=1
switch 1
            case Namelist{4}.nwp_model_domain==3 & strcmp(Namelist{4}.nwp_model{1},'ETA')
                Namelist{5}.Analog.lead_times=[12:1:37] % rember lead 1=0 13=12
                Namelist{5}.Analog.lead_delta=Namelist{5}.Analog.lead_times(2)-Namelist{5}.Analog.lead_times(1)
    
            case Namelist{4}.nwp_model_domain==3 & strcmp(Namelist{4}.nwp_model{1},'WRF')
                Namelist{5}.Analog.lead_times=[12:1:36] % rember lead 1=0 13=12
                Namelist{5}.Analog.lead_delta=Namelist{5}.Analog.lead_times(2)-Namelist{5}.Analog.lead_times(1)
    
            case Namelist{4}.nwp_model_domain==2
                Namelist{5}.Analog.lead_times=[12:3:36] % rember lead 1=0 13=12
                Namelist{5}.Analog.lead_delta=Namelist{5}.Analog.lead_times(2)-Namelist{5}.Analog.lead_times(1)
    
            case Namelist{4}.nwp_model_domain==1
                Namelist{5}.Analog.lead_times=[12:3:36] % rember lead 1=0 13=12
                Namelist{5}.Analog.lead_delta=Namelist{5}.Analog.lead_times(2)-Namelist{5}.Analog.lead_times(1)
    

        end


for i=1:length(turbine_time_series(1,7).data{2,2})
    leadtime_vector(i)=Namelist{5}.Analog.lead_times(Namelist_Analog_lead_times_counter);
    Namelist_Analog_lead_times_counter=Namelist_Analog_lead_times_counter+1;
    if Namelist_Analog_lead_times_counter==length(Namelist{5}.Analog.lead_times)+1;
        Namelist_Analog_lead_times_counter=1;
    end
end
end

