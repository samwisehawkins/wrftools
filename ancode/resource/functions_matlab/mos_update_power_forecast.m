function [ time_serie_power_forecast ] = mos_update_power_forecast( good_turbine_data, time_serie_nwp_forecast,time_serie_power_forecast,Namelist )
%MOS_UPDATE_POWER_FORECAST updates the power forecast with mos corrected
%values
%   Detailed explanation goes here
 power_curve=get_power_curve(Namelist)
               
switch 1
    
    case strcmp(Namelist{7}.mos_field,'windspeed')
        
    switch 1
        case Namelist{5}.w2p_method==1
       
       switch 1
           case strcmp(Namelist{7}.mos_metod,'simple_linear_regression')
        
                % get index for wind speed entry 
                for i=1:length(time_serie_power_forecast{3,6})
                confidence_residual=cell2mat(time_serie_power_forecast{1,16}(1,str2num(time_serie_power_forecast{1,3}(i,:))+1));
                [min_difference, windspeed_index] = min(abs(power_curve{1,2} -time_serie_power_forecast{3,6}(i) ));
                % get index for air density entry either 10 m or at 
                % get index for upper wind speed on current lead time
                [min_difference, windspeed_index_upper_conf] = min(abs(power_curve{1,2} -(time_serie_power_forecast{3,6}(i)+confidence_residual) ));
                [min_difference, windspeed_index_lower_conf] = min(abs(power_curve{1,2} -(time_serie_power_forecast{3,6}(i)-confidence_residual) ));

                    if Namelist{5}.w2p_use_10m_rho
                        [min_difference, air_density_index] = min(abs(power_curve{1,1} - time_serie_nwp_forecast{1,12}(i)));
                    else
                        [min_difference, air_density_index] = min(abs(power_curve{1,1} - time_serie_nwp_forecast{1,13}(i)));
                    end % if 
                 
                time_serie_power_forecast{3,4}(i)=power_curve{1,3}{air_density_index}(windspeed_index);
                time_serie_power_forecast{4,4}='Predicted power per turbine mos correted';

                time_serie_power_forecast{5,4}(i)=power_curve{1,3}{air_density_index}(windspeed_index_upper_conf);
                time_serie_power_forecast{6,4}='Predicted power per turbine mos correted upper 95 % condfidence';

                time_serie_power_forecast{7,4}(i)=power_curve{1,3}{air_density_index}(windspeed_index_lower_conf);
                time_serie_power_forecast{8,4}='Predicted power per turbine mos correted lower 95 % condfidence';

            % get index for forecast timestamå in observations and take the
            % number of producing turbines
             obs_indx=find(datenum(time_serie_power_forecast{1,2}(i,:),Namelist{1}.datstr_general_format)==datenum(good_turbine_data{1,2},Namelist{1}.datstr_general_format));%   
             nr_turbines=good_turbine_data{1,1}(obs_indx);
                          
             if isempty(obs_indx)
                 time_serie_power_forecast{3,5}(i)=time_serie_power_forecast{1,4}(i)*(0);
                 time_serie_power_forecast{3,7}(i,:)=-99; % nacelle wind 
                 time_serie_power_forecast{3,8}(i,:)=-99; % nacelle wind direction
                 time_serie_power_forecast{3,10}(i,:)=-99; % observed total power production
             else
                 time_serie_power_forecast{3,5}(i)=time_serie_power_forecast{3,4}(i)*nr_turbines;   
                 time_serie_power_forecast{5,5}(i)=time_serie_power_forecast{5,4}(i)*nr_turbines;   
                 time_serie_power_forecast{7,5}(i)=time_serie_power_forecast{7,4}(i)*nr_turbines;   

                if mod(i,100)==0
                    disp(strcat('Powerforecasting completed out to :',datestr(datenum(time_serie_power_forecast{1,2}(i,:),Namelist{1}.datstr_general_format),Namelist{1}.datstr_general_format)));
                end 
             end %if
        
             time_serie_power_forecast{4,5}='Mos corrected deterministic total power forecast'   ;
             time_serie_power_forecast{6,5}='Mos corrected deterministic total power forecast upper 95% confidence';
             time_serie_power_forecast{8,5}='Mos corrected deterministic total power forecast lower 95% confidence' ;  

            end % for 
% MAKE SURE FORMAT IS RIGHT 
[m n]=size(time_serie_power_forecast{3,5})
        if m==1
            time_serie_power_forecast{3,5}=double(time_serie_power_forecast{3,5})'
            time_serie_power_forecast{3,4}=double(time_serie_power_forecast{3,4})'
            time_serie_power_forecast{3,5}=double(time_serie_power_forecast{3,5})'
            time_serie_power_forecast{5,4}=double(time_serie_power_forecast{5,4})'
            time_serie_power_forecast{7,4}=double(time_serie_power_forecast{7,4})'
            time_serie_power_forecast{5,5}=double(time_serie_power_forecast{5,5})'
            time_serie_power_forecast{7,5}=double(time_serie_power_forecast{7,5})'
        else
                time_serie_power_forecast{3,5}=double(time_serie_power_forecast{3,5})
                time_serie_power_forecast{3,4}=time_serie_power_forecast{3,4}
        end
        
        
        %begin test
           case strcmp(Namelist{7}.mos_metod,'multivariate_regression')
                % get index for wind speed entry 
                for i=1:length(time_serie_power_forecast{9,6})
                confidence_residual=cell2mat(time_serie_power_forecast{4,16}(1,str2num(time_serie_power_forecast{1,3}(i,:))+1));
                [min_difference, windspeed_index] = min(abs(power_curve{1,2} -time_serie_power_forecast{9,6}(i) ));
                % get index for air density entry either 10 m or at 
                % get index for upper wind speed on current lead time
                [min_difference, windspeed_index_upper_conf] = min(abs(power_curve{1,2} -(time_serie_power_forecast{9,6}(i)+confidence_residual) ));
                [min_difference, windspeed_index_lower_conf] = min(abs(power_curve{1,2} -(time_serie_power_forecast{9,6}(i)-confidence_residual) ));

                    if Namelist{5}.w2p_use_10m_rho
                        [min_difference, air_density_index] = min(abs(power_curve{1,1} - time_serie_nwp_forecast{1,12}(i)));
                    else
                        [min_difference, air_density_index] = min(abs(power_curve{1,1} - time_serie_nwp_forecast{1,13}(i)));
                    end % if 
                 
                time_serie_power_forecast{15,4}(i)=power_curve{1,3}{air_density_index}(windspeed_index);
                time_serie_power_forecast{16,4}='Predicted power per turbine multivriate mos correted';

                time_serie_power_forecast{17,4}(i)=power_curve{1,3}{air_density_index}(windspeed_index_upper_conf);
                time_serie_power_forecast{18,4}='Predicted power per turbine multivriate mos correted upper 95 % condfidence';

                time_serie_power_forecast{19,4}(i)=power_curve{1,3}{air_density_index}(windspeed_index_lower_conf);
                time_serie_power_forecast{20,4}='Predicted power per turbine multivriate mos correted lower 95 % condfidence';

            % get index for forecast timestamå in observations and take the
            % number of producing turbines
             obs_indx=find(datenum(time_serie_power_forecast{1,2}(i,:),Namelist{1}.datstr_general_format)==datenum(good_turbine_data{1,2},Namelist{1}.datstr_general_format));%   
             nr_turbines=good_turbine_data{1,1}(obs_indx);
                          
             if isempty(obs_indx)
                 time_serie_power_forecast{15,5}(i)=time_serie_power_forecast{1,4}(i)*(0);
                 time_serie_power_forecast{15,7}(i,:)=-99; % nacelle wind 
                 time_serie_power_forecast{15,8}(i,:)=-99; % nacelle wind direction
                 time_serie_power_forecast{15,10}(i,:)=-99; % observed total power production
             else
                 time_serie_power_forecast{15,5}(i)=time_serie_power_forecast{15,4}(i)*nr_turbines;   
                 time_serie_power_forecast{17,5}(i)=time_serie_power_forecast{17,4}(i)*nr_turbines;   
                 time_serie_power_forecast{19,5}(i)=time_serie_power_forecast{19,4}(i)*nr_turbines;   

                if mod(i,100)==0
                    disp(strcat('Powerforecasting completed out to :',datestr(datenum(time_serie_power_forecast{1,2}(i,:),Namelist{1}.datstr_general_format),Namelist{1}.datstr_general_format)));
                end 
             end %if
        
             time_serie_power_forecast{16,5}='Mulitivariate Mos corrected deterministic total power forecast'   ;
             time_serie_power_forecast{18,5}='Mulitivariate Mos corrected deterministic total power forecast upper 95% confidence';
             time_serie_power_forecast{20,5}='Mulitivariate Mos corrected deterministic total power forecast lower 95% confidence' ;  

            end % for 
% MAKE SURE FORMAT IS RIGHT 
[m n]=size(time_serie_power_forecast{3,5})
        if m==1
            time_serie_power_forecast{15,5}=double(time_serie_power_forecast{15,5})'
            time_serie_power_forecast{15,4}=double(time_serie_power_forecast{15,4})'
            time_serie_power_forecast{15,5}=double(time_serie_power_forecast{15,5})'
            time_serie_power_forecast{17,4}=double(time_serie_power_forecast{17,4})'
            time_serie_power_forecast{19,4}=double(time_serie_power_forecast{19,4})'
            time_serie_power_forecast{17,5}=double(time_serie_power_forecast{17,5})'
            time_serie_power_forecast{19,5}=double(time_serie_power_forecast{19,5})'
        else
                time_serie_power_forecast{15,5}=double(time_serie_power_forecast{15,5})
                time_serie_power_forecast{15,4}=time_serie_power_forecast{15,4}
        end
        
        %end multivariate 
        
        
        
        
        
           case strcmp(Namelist{7}.mos_metod,'univariate_regression_sector_wice')
               for i=1:length(time_serie_power_forecast{3,6})
                       % sector wice and lead time loop
                       % detmined sector and update only that one
                           if time_serie_nwp_forecast{1,9}(i)==360
                               nwp_wind__direction_index=1
                           else
                            nwp_wind__direction_index=find(time_serie_nwp_forecast{1,9}(i)>=Namelist{7}.wdir_lower &(Namelist{7}.wdir_upper>time_serie_nwp_forecast{1,9}(i)));
                           end
                        confidence_residual=cell2mat(time_serie_power_forecast{3,16}(str2num(time_serie_power_forecast{1,3}(i,:))+1,nwp_wind__direction_index));
                        [min_difference, windspeed_index] = min(abs(power_curve{1,2} -time_serie_power_forecast{5,6}(i) ));
                        % get index for air density entry either 10 m or at 
                        % get index for upper wind speed on current lead time
                        [min_difference, windspeed_index_upper_conf] = min(abs(power_curve{1,2} -(time_serie_power_forecast{5,6}(i)+confidence_residual) ));
                        [min_difference, windspeed_index_lower_conf] = min(abs(power_curve{1,2} -(time_serie_power_forecast{5,6}(i)-confidence_residual) ));
                        if Namelist{5}.w2p_use_10m_rho
                            [min_difference, air_density_index] = min(abs(power_curve{1,1} - time_serie_nwp_forecast{1,12}(i)));
                        else
                            [min_difference, air_density_index] = min(abs(power_curve{1,1} - time_serie_nwp_forecast{1,13}(i)));
                        end % if
                             time_serie_power_forecast{9,4}(i)=power_curve{1,3}{air_density_index}(windspeed_index);
                            time_serie_power_forecast{10,4}='Predicted power per turbine mos correted in wind-dir sector';
                            time_serie_power_forecast{11,4}(i)=power_curve{1,3}{air_density_index}(windspeed_index_upper_conf);
                            time_serie_power_forecast{12,4}='Predicted power per turbine mos correted in wind-dir sector upper 70 % condfidence';
                            time_serie_power_forecast{13,4}(i)=power_curve{1,3}{air_density_index}(windspeed_index_lower_conf);
                            time_serie_power_forecast{14,4}='Predicted power per turbine mos correted wind-dir lower 20 % condfidence';
                            
                            obs_indx=find(datenum(time_serie_power_forecast{1,2}(i,:),Namelist{1}.datstr_general_format)==datenum(good_turbine_data{1,2},Namelist{1}.datstr_general_format));%   
                            nr_turbines=good_turbine_data{1,1}(obs_indx);
                          
             if isempty(obs_indx)
                 time_serie_power_forecast{9,5}(i)=time_serie_power_forecast{1,4}(i)*(0);
                 time_serie_power_forecast{9,7}(i,:)=-99; % nacelle wind 
                 time_serie_power_forecast{9,8}(i,:)=-99; % nacelle wind direction
                 time_serie_power_forecast{9,10}(i,:)=-99; % observed total power production
             else
                 %time_serie_power_forecast{9,5}(i)=time_serie_power_forecast{3,4}(i)*nr_turbines;   
                 %time_serie_power_forecast{11,5}(i)=time_serie_power_forecast{5,4}(i)*nr_turbines;   
                 %time_serie_power_forecast{13,5}(i)=time_serie_power_forecast{7,4}(i)*nr_turbines;   
% Gammel kode ændret til                  
                 time_serie_power_forecast{9,5}(i)=time_serie_power_forecast{9,4}(i)*nr_turbines;   
                 time_serie_power_forecast{11,5}(i)=time_serie_power_forecast{11,4}(i)*nr_turbines;   
                 time_serie_power_forecast{13,5}(i)=time_serie_power_forecast{13,4}(i)*nr_turbines;   
                 
                if mod(i,100)==0
                    disp(strcat('Powerforecasting completed out to :',datestr(datenum(time_serie_power_forecast{1,2}(i,:),Namelist{1}.datstr_general_format),Namelist{1}.datstr_general_format)));
                end 
             end %if
        
             time_serie_power_forecast{10,5}='Sectorvice Mos corrected  total power forecast'   ;
             time_serie_power_forecast{12,5}='Sectorvice Mos corrected deterministic total power forecast upper 95% confidence';
             time_serie_power_forecast{14,5}='Sectorvice Mos corrected deterministic total power forecast lower 95% confidence' ;  

               end % lead time loop
               if Namelist{9}.plot_sector_corrections==1;
                                      test=1;
               end
       end % switch Namelist{7}.mos_metod
      end % switch w2p
     end %switch Namelist{7}.mos_field


end

