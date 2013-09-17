function [ var_std ] = get_std_on_nwp_variables( data_set,i );
%GET_STD_ON_NWP_VARIABLES Summary of this function goes here
% computes the climetolical standard diviation on all phycical varoables to
% be used to normalize anlogs findings
% analogs
%i is index in alog state vector  
%   Detailed explanation goes here
% special attention is brought on wind diretipn being a circular variable 
switch 1
    
    case  isequal(regexpi(data_set.colheaders(i),'Bulk_Richardson'),{1})
            idx=find(data_set.data(:,i)>-10&data_set.data(:,i)<10);
            var_std=std(data_set.data(idx,i));
    
    case isequal(regexpi(data_set.colheaders(i),'wdir'),{1})
            idx=find(data_set.data(:,i)>0&data_set.data(:,i)<365);
            var_std=stdTNcirc(data_set.data(idx,i),-999,1,1);%stdTNcirc(time_serie_nwp_forecast{1,i}, mv, var_set, isCircular);
     
        
    case  isequal(regexpi(data_set.colheaders(i),'Surface_Preasure'),{1})
            idx=find(data_set.data(:,i)>90000&data_set.data(:,i)<110000);
            var_std=std(data_set.data(idx,i));
    case 1 % if not any of the above thern always do this
            
            idx=find(data_set.data(:,i)>0&data_set.data(:,i)<80);
            var_std=std(data_set.data(idx,i));
            
        end
end

