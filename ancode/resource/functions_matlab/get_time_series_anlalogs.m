function [model_ANALOG_5 model_ANALOG_10 model_ANALOG_15 model_ANALOG_20 model_ANALOG_25 ]=get_time_series_anlalogs(time_serie_power_forecast_05_analogs, time_serie_power_forecast_10_analogs, time_serie_power_forecast_15_analogs, time_serie_power_forecast_20_analogs, time_serie_power_forecast_25_analogs, idx_non_nan);
          
%GET_TIME_SERIES_ANLALOGS Summary of this function goes here
%   Detailed explanation goes here
model_ANALOG_5=time_serie_power_forecast_05_analogs{2,2}(idx_non_nan) ;
model_ANALOG_10=time_serie_power_forecast_10_analogs{2,2}(idx_non_nan) ;
model_ANALOG_15=time_serie_power_forecast_15_analogs{2,2}(idx_non_nan) ;
model_ANALOG_20=time_serie_power_forecast_20_analogs{2,2}(idx_non_nan) ;
model_ANALOG_25=time_serie_power_forecast_25_analogs{2,2}(idx_non_nan);

end

