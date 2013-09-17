
function [rmse bias crmse] = RMSEdecomp_all(obs, Data, par)

%
   if (nargin < 3)
       par.mv = -999;
   end

% Calculations
   T = length(Data(:, 1));       % Number of entries
   N = length(Data(1, :));      % Number of members
   if(length(obs(1, :)) == 1)
       obs = repmat(obs, 1, N);
   end

% Error calculation
   error  = zeros(T, N);
   crmse = zeros(N, 1);
   rmse_s = zeros(N, 1);
   rmse   = zeros(N, 1);
   for i = 1:N
       counter = 0;
       I1 = find(obs(:, i) ~=par.mv);
       %I1 = find(obs(:, i) > 0);
       I2 = find(isfinite(obs(:, i)));
       I3 = find(Data(:, i) ~= par.mv);
       %I3 = find(Data(:, i) > 0);
       I4 = find(isfinite(Data(:, i)));

       I = intersect(I1, I2);
       I = intersect(I , I3);
       I = intersect(I , I4);
       if(length(I) == 0)
           rmse(i) = par.mv;
           rmse_s(i) = par.mv;
           crmse(i) = par.mv;
       else


           bias      = mean(-obs(I, i) + Data(I, i));
           rmse_s(i) = bias;
           crmse(i) = sqrt(mean( ((Data(I, i) - mean(Data(I, i))) - (obs(I, i) - mean(obs(I,i)))).^2 ));
           rmse(i) = sqrt(mean((Data(I, i) - obs(I, i)).^2));
       end
   end



