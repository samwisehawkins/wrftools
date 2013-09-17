function [ distance_on_lead_time ] = get_distance_on_lead_time( Historical_forecast_vector,forecast_vector,Namelist,leadtime)
%GET_DISTANCE_ON_LEAD_TIME Summary of this function goes here
%   Detailed explanation goes here
% first nmake sure all have same length


for i=1:length(Namelist{5}.Analog.state_vector_idx)
    Length_t=length(Historical_forecast_vector.var_data{2,i});
    Length_t_minus_1=length(Historical_forecast_vector.var_data{4,i});
    Length_t_plus_1=length(Historical_forecast_vector.var_data{6,i});
    
    length_sorted=sort([Length_t Length_t_minus_1 Length_t_plus_1],'ascend');% make sure shortest is the fist 
    if length_sorted(1)==0
        length_sorted(1)=length_sorted(2);
    end
    forecast_vector.var_data{4,i};
    forecast_vector.var_data{6,i};
    
switch 1
    case strcmp('Valid_time',Historical_forecast_vector.var_data{1,i}) | strcmp('Lead time h',Historical_forecast_vector.var_data{1,i}) | strcmp('Lead time',Historical_forecast_vector.var_data{1,i}) | strcmp('Lead time h',Historical_forecast_vector.var_data{1,i}) | strcmp('valid_time',Historical_forecast_vector.var_data{1,i}) 
        % we do not calculate distance if filed is  walid time or lead time
    
    case strcmp('wdir 10m',Historical_forecast_vector.var_data{1,i})

        if leadtime~=25
            factor_1=(Namelist{1,5}.Analog.weights_state_vector_idx(i)/Historical_forecast_vector.var_data{7,i});
            factor_2=get_wind_dir_diff(forecast_vector.var_data{2,i},Historical_forecast_vector.var_data{2,i}(1:length_sorted(1)));
            factor_3=get_wind_dir_diff(forecast_vector.var_data{4,i},Historical_forecast_vector.var_data{4,i}(1:length_sorted(1)));
            factor_4=get_wind_dir_diff(forecast_vector.var_data{6,i},Historical_forecast_vector.var_data{6,i}(1:length_sorted(1)));
            %tempo(i,:)= (Namelist{1,5}.Analog.weights_state_vector_idx(i)/Historical_forecast_vector.var_data{7,i})* ...
            %sqrt(((forecast_vector.var_data{2,i}-Historical_forecast_vector.var_data{2,i}(1:length_sorted(1))).^2)+ ...
            %((forecast_vector.var_data{4,i}-Historical_forecast_vector.var_data{4,i}(1:length_sorted(1))).^2)+ ...
            %((forecast_vector.var_data{6,i}-Historical_forecast_vector.var_data{6,i}(1:length_sorted(1))).^2))
            tempo(i,:)= factor_1* ...
            sqrt(((factor_2).^2)+ ...
            ((factor_3).^2)+ ...
            ((factor_4).^2));
        else
             %   tempo(i,:)= (Namelist{1,5}.Analog.weights_state_vector_idx(i)/Historical_forecast_vector.var_data{7,i})*sqrt(((forecast_vector.var_data{2,i}-Historical_forecast_vector.var_data{2,i}(1:length_sorted(1))).^2)+((forecast_vector.var_data{4,i}-Historical_forecast_vector.var_data{4,i}(1:length_sorted(1))).^2))
            factor_1=(Namelist{1,5}.Analog.weights_state_vector_idx(i)/Historical_forecast_vector.var_data{7,i}); % weights and normalize by std of variable
            factor_2=get_wind_dir_diff(forecast_vector.var_data{2,i},Historical_forecast_vector.var_data{2,i}(1:length_sorted(1)));
            factor_3=get_wind_dir_diff(forecast_vector.var_data{4,i},Historical_forecast_vector.var_data{4,i}(1:length_sorted(1)));
            tempo(i,:)= factor_1* ...
            sqrt(((factor_2).^2)+ ...
            ((factor_3).^2)) ;
        end 

    case 1 % if not above always do this
              % weight and standard diviation
        if leadtime~=25
                tempo(i,:)= (Namelist{1,5}.Analog.weights_state_vector_idx(i)/Historical_forecast_vector.var_data{7,i})*sqrt(((forecast_vector.var_data{2,i}-Historical_forecast_vector.var_data{2,i}(1:length_sorted(1))).^2)+((forecast_vector.var_data{4,i}-Historical_forecast_vector.var_data{4,i}(1:length_sorted(1))).^2)+((forecast_vector.var_data{6,i}-Historical_forecast_vector.var_data{6,i}(1:length_sorted(1))).^2));
        else
                tempo(i,:)= (Namelist{1,5}.Analog.weights_state_vector_idx(i)/Historical_forecast_vector.var_data{7,i})*sqrt(((forecast_vector.var_data{2,i}-Historical_forecast_vector.var_data{2,i}(1:length_sorted(1))).^2)+((forecast_vector.var_data{4,i}-Historical_forecast_vector.var_data{4,i}(1:length_sorted(1))).^2));
        end 
    end %switch
end
distance_on_lead_time=sum(tempo,1);