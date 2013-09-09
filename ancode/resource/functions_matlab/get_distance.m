function [ distance] = get_distance( forecast_vector,Namelist,data_set)
%GET_DISTANCE_ON_LEAD_TIME Summary of this function goes here
% This is the analog metrix , the distance the current forecast has to all previous forecast is calculate as a weighted sum over the pridictor vaiables  forecast vector is 
%We start to calculate the distance from initial prediction nr 2 as we sum over the difference from initial forecast 1 to initial forecast 3 
%with the  first nmake sure all have same length

lengh_data_set=length(data_set.data(:,5));
idx_t_minus_one=linspace(1,lengh_data_set-2,lengh_data_set-2);
idx=linspace(2,lengh_data_set-1,lengh_data_set-2);
idx_t_plus_one=linspace(3,lengh_data_set,lengh_data_set-2);

for i=1:length(Namelist{5}.Analog.state_vector_idx) % loop through all the analog predictor/state variables 
    switch 1
    case strcmp('Valid_time',data_set.colheaders(1,Namelist{5}.Analog.state_vector_idx(i))) | ...
         strcmp('Lead_time',data_set.colheaders(Namelist{5}.Analog.state_vector_idx(i))) ... 
         | strcmp('Lead_time',data_set.colheaders(Namelist{5}.Analog.state_vector_idx(i))) | strcmp('Lead time h',data_set.colheaders(1,Namelist{5}.Analog.state_vector_idx(i))) ...
         | strcmp('valid_time',data_set.colheaders(1,Namelist{5}.Analog.state_vector_idx(i))) | strcmp('Init_time',data_set.colheaders(1,Namelist{5}.Analog.state_vector_idx(i))) 
        % we do not calculate distance if filed is  walid time or lead time
    
    case not(cellfun('isempty',regexpi(data_set.colheaders(Namelist{5}.Analog.state_vector_idx(i)),'wdir')))
        
            var_std=get_std_on_nwp_variables( data_set,Namelist{5}.Analog.state_vector_idx(i));
            factor_1=(Namelist{1,5}.Analog.weights_state_vector_idx(i)/var_std);
            factor_2=get_wind_dir_diff(forecast_vector.var_data{2,i},data_set.data(idx,Namelist{5}.Analog.state_vector_idx(i)));
            factor_3=get_wind_dir_diff(forecast_vector.var_data{4,i},data_set.data(idx_t_minus_one,Namelist{5}.Analog.state_vector_idx(i)));
            factor_4=get_wind_dir_diff(forecast_vector.var_data{6,i},data_set.data(idx_t_plus_one,Namelist{5}.Analog.state_vector_idx(i)));
            
            tempo(i,:)= factor_1* ...
            sqrt(((factor_2).^2)+ ...
            ((factor_3).^2)+ ...
            ((factor_4).^2));
 
    case 1 % if not above always do this
              var_std=get_std_on_nwp_variables( data_set,Namelist{5}.Analog.state_vector_idx(i));
              tempo(i,:)= (Namelist{1,5}.Analog.weights_state_vector_idx(i)/var_std)*...
              sqrt(((forecast_vector.var_data{2,i}-data_set.data(idx,Namelist{5}.Analog.state_vector_idx(i))).^2)+...
              ((forecast_vector.var_data{4,i}-data_set.data(idx_t_minus_one,Namelist{5}.Analog.state_vector_idx(i))).^2)+...
              ((forecast_vector.var_data{6,i}-data_set.data(idx_t_plus_one,Namelist{5}.Analog.state_vector_idx(i))).^2));
          
    end %switch
end
distance=sum(tempo,1);