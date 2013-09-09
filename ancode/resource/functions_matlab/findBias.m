function [ bias_stat] = findBias(obs, ens, par)
%FINDBIAS Summary of this function goes here
%   Detailed explanation goes here
   [T,N] = size(obs);
   bias_stat = zeros(N);

   for i = 1:N
      I = intersect(find(obs(:, i) ~= par.mv), find(ens(:, i) ~= par.mv));
      %I = intersect(find(obs(:, i) > 0), find(ens(:, i) > 0));
      flag = isempty(I);
      if (flag ~= 1)
         sz = size(I);
         bias_stat(i) = mean(-obs(I, i) + ens(I, i));
      else
         bias_stat(i) = par.mv;
      end
   end

return


end

