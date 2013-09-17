function [ succes ] = test_do_dispersion_diagram_concanated_turbines_10_analogs( )
%DO_ACCURACY_NWP_ANALYSIS Summary of this function goes here
%   Detailed explanation goes here
close all
   
    for j=[1:20]
        obs=[];model=[];model_ensembles=[];model_ensembles_variance=[];
            % concanate loop
            % first get the normali distributed dataset
              model_ensembles=randn(100,10);
            % than take the freeking obs out of that one 
                obs=model_ensembles(:,2);
                model=mean(model_ensembles,2); % model values out of a normal distributed randam numbers 

            for i=1:100
                model_ensembles_variance=var(model_ensembles(i,:))
            end
                [ETA_rmse_10(j) ETA_bias_10(j) ETA_crmse_10(j)] = RMSEdecomp_all(obs, model);
                 ETA_spread_10(j)=sqrt(mean(model_ensembles_variance))                   
    end
    plot(ETA_rmse_10,'r*') 
    hold on 
    plot(ETA_spread_10,'b:') 
    
 end
