function [ analogs_lead_times ] = get_analog_lead_times( Namelist )
%GET_ANALOG_LEAD_TIMES Summary of this function goes here
%   Detailed explanation goes here
switch 1
            case Namelist{4}.nwp_model_domain==3
                analogs_lead_times=[12:1:37] % rember lead 1=0 13=12
                Namelist{5}.Analog.lead_delta=analogs_lead_times(2)-analogs_lead_times(1)
    
            case Namelist{4}.nwp_model_domain==2
                analogs_lead_times=[12:3:36] % rember lead 1=0 13=12
                Namelist{5}.Analog.lead_delta=analogs_lead_times(2)-analogs_lead_times(1)
    
            case Namelist{4}.nwp_model_domain==1
                analogs_lead_times=[12:3:36] % rember lead 1=0 13=12
                Namelist{5}.Analog.lead_delta=analogs_lead_times(2)-analogs_lead_times(1)
    

        end




end

