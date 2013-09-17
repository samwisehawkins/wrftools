function [succes]=do_mahalanobis(Namelist,good_turbine_data,time_serie_nwp_forecast,num_obs_dates,clean_turbine_data)

%X = mvnrnd([0;0],[1 .9;.9 1],100);
%Y = [1 1;1 -1;-1 1;-1 -1];

%addpath(genpath('C:\Users\jnini\MATLAB\work\AnEn\functions'))
%[ Namelist ]=set_Namelist_N30471( )

%get sprogø data 
%[good_turbine_data time_serie_nwp_forecast num_obs_dates clean_turbine_data]=load_data(Namelist)
%                        wind speed                  Power
X=[good_turbine_data(1,7).power_production{1,4} good_turbine_data(1,7).power_production{1,3}]

% to be made as function of turbine numer and nwp variable
%looping over all turbine and all relevant predictor variables 
counter=0
turbine_idx=1;
%nwp_var=[6 15 19 23 27 31 35 39 ] %WRF wind speeds at all levels 

    for nwp_var=[6 27] %ECMWF windspeeds at 10 and 100 
        counter=counter+1;
        Y.data(counter,:,:)=get_Y(good_turbine_data,turbine_idx,time_serie_nwp_forecast,Namelist,nwp_var);
        Y.names(counter)=cellstr(time_serie_nwp_forecast{2,nwp_var});
        if not(isempty(time_serie_nwp_forecast{1,nwp_var-1}))
            Y.heights(counter)=time_serie_nwp_forecast{1,nwp_var-1}(1);
        end
    end
    Y.heights(1)=10;Y.heights(2)=13.59;
 % do the mahalanobis distance and the spearman rank correlation for each predictor variable     
[z m n ]=size(Y.data)
for mahalanobis_counter=1:z
    temp=squeeze(Y.data(mahalanobis_counter,:,:));
    D(mahalanobis_counter) = sum(mahal(temp,X)); % Mahalanobis
    Corr_obs_pred(mahalanobis_counter)=corr(temp(:,1),temp(:,2),'type','Spearman')
end

for mahalanobis_counter=1:z
    vector=[1:z];idx=find(vector==mahalanobis_counter)
    %weight_vector=ones(1,z);
    %weight_vector(idx)=1;
        D_weight_vector=D
        D_weight_vector(idx)=1
        Weights(mahalanobis_counter)=prod(D_weight_vector)./(prod(D_weight_vector)*D(mahalanobis_counter))
        end
Weights=Weights./(sum(Weights)) % normalize
Weights_cor=Corr_obs_pred./sum(Corr_obs_pred)
bar(D);grid on;set(gca,'xticklabel',Y.heights,'fontsize',20);
xlabel('WRF computational heights in m','fontsize',20);ylabel('sum of Mahalonobis distances','fontsize',20)

figure;
bar(Weights); set(gca,'xticklabel',Y.heights,'fontsize',20);set(gca,'ylim',[0.08 .17]);grid on
ylabel('Mahal weights')

figure
bar(Weights_cor); set(gca,'xticklabel',Y.heights,'fontsize',20);set(gca,'ylim',[0.08 .17]);grid on
ylabel('Spearman Weights ')
xlabel('WRF computational heights in m','fontsize',20);grid on

% now test with only 1 dimentional obs and forecast 

for mahalanobis_counter=1:z
    pred=squeeze(Y.data(mahalanobis_counter,:,1))';
    obs=squeeze(Y.data(mahalanobis_counter,:,2))';
    D(mahalanobis_counter) = sum(mahal(pred,obs)); % Mahalanobis
end

for mahalanobis_counter=1:z
    vector=[1:z];idx=find(vector==mahalanobis_counter)
    %weight_vector=ones(1,z);
    %weight_vector(idx)=1;
        D_weight_vector=D
        D_weight_vector(idx)=1
        Weights(mahalanobis_counter)=prod(D_weight_vector)./(prod(D_weight_vector)*D(mahalanobis_counter))
end
Weights=Weights./(sum(Weights)) % normalize
bar(D);grid on;set(gca,'xticklabel',Y.heights,'fontsize',20);
xlabel('WRF computational heights in m','fontsize',20);ylabel('sum of Mahalonobis distances 1 Dimention','fontsize',20)
figure;bar(Weights); set(gca,'xticklabel',Y.heights,'fontsize',20);
xlabel('WRF computational heights in m','fontsize',20);ylabel('Normalized weights','fontsize',20);grid on

figure 
subplot(5,2,1)
plot(X(:,1),X(:,2),'b*');set (gca,'ylim',[0 3000],'xlim',[0 20]);grid on
subplot(5,2,2)
plot(Y.data(1,:,1),Y.data(1,:,2),'b*');set (gca,'ylim',[0 3000],'xlim',[0 20]);grid on
subplot(5,2,3)
plot(Y.data(2,:,1),Y.data(1,:,2),'b*');set (gca,'ylim',[0 3000],'xlim',[0 20]);grid on
subplot(5,2,4)
plot(Y.data(3,:,1),Y.data(1,:,2),'b*');set (gca,'ylim',[0 3000],'xlim',[0 20]);grid on
subplot(5,2,5)
plot(Y.data(4,:,1),Y.data(1,:,2),'b*');set (gca,'ylim',[0 3000],'xlim',[0 20]);grid on
subplot(5,2,6)
plot(Y.data(5,:,1),Y.data(1,:,2),'b*');set (gca,'ylim',[0 3000],'xlim',[0 20]);grid on
subplot(5,2,7)
plot(Y.data(6,:,1),Y.data(1,:,2),'b*');set (gca,'ylim',[0 3000],'xlim',[0 20]);grid on
subplot(5,2,8)
plot(Y.data(7,:,1),Y.data(1,:,2),'b*');set (gca,'ylim',[0 3000],'xlim',[0 20]);grid on
subplot(5,2,9)
plot(Y.data(8,:,1),Y.data(1,:,2),'b*');set (gca,'ylim',[0 3000],'xlim',[0 20]);grid on


succes=true

