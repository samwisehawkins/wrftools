function [ time_serie_nwp_forecast ] = get_diagnostics_on_nwp_variables(time_serie_nwp_forecast,Namelist);
%GET_DIAGNOSTICS_ON_NWP_VARIABLES Summary of this function goes here
%   Detailed explanation goes here
switch 1
    case strcmp(Namelist{4}.nwp_model{1},'WRF')==1
        [m n]=size(time_serie_nwp_forecast);
        time_serie_nwp_forecast{2,n+1}='Rotor-plane-Shear'
        time_serie_nwp_forecast{2,n+2}='Bulk Richardson number'
        time_serie_nwp_forecast{6,n+1}='Rotor-plane-Shear heights'
        time_serie_nwp_forecast{6,n+2}='Bulk Richardson heights'
        
        [shear_h_lower_idx shear_h_upper_idx BR_h_lower_idx BR_h_upper_idx ]=get_height_index(Namelist);
        time_serie_nwp_forecast{5,n+1}(1)=time_serie_nwp_forecast(1,shear_h_lower_idx);
        time_serie_nwp_forecast{5,n+1}(2)=time_serie_nwp_forecast(1,shear_h_upper_idx);
        if BR_h_lower_idx==1
            time_serie_nwp_forecast{5,n+2}(1)=0;
        else
            time_serie_nwp_forecast{5,n+2}(1)=time_serie_nwp_forecast(1,BR_h_lower_idx);
        end
        dh_shear=cell2mat(time_serie_nwp_forecast{5,n+1}(2))- cell2mat(time_serie_nwp_forecast{5,n+1}(1));
        d_wspd=cell2mat(time_serie_nwp_forecast(1,shear_h_upper_idx+1))-cell2mat(time_serie_nwp_forecast(1,shear_h_lower_idx+1));
       time_serie_nwp_forecast{1,n+1}=d_wspd./dh_shear;
        
end % switch

dav='hej'

end

