function [ lead_times ] = set_analog_leadtimes(Namelist,init)
%UNTITLED Summary of this function goes here
%   Detailed explanation goes here
switch 1
            case Namelist{4}.nwp_model_domain==3 & init==1
                lead_times=[12:1:47] % rember lead 1=0 13=12
                
            case Namelist{4}.nwp_model_domain==3 & init==2
                lead_times=[12:1:47] % rember lead 1=0 13=12
            
            case Namelist{4}.nwp_model_domain==2 & init==1
                lead_times=[12:3:47] % rember lead 1=0 13=12
                
            case Namelist{4}.nwp_model_domain==2 & init==2
                lead_times=[12:3:47] % rember lead 1=0 13=12
           
            case Namelist{4}.nwp_model_domain==1 & init==1
                lead_times=[12:3:47] % rember lead 1=0 13=12
                
            case Namelist{4}.nwp_model_domain==1 & init==2
                lead_times=[12:3:47] % rember lead 1=0 13=12
           
        end

end

