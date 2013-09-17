function [ correl ] = findCorr(obs, ens, par)

   [T,N] = size(obs);
   correl = zeros(N);

   for i = 1:N
      I = intersect(find(obs(:, i) ~= par.mv), find(ens(:, i) ~= par.mv));
      %I = intersect(find(obs(:, i) > 0), find(ens(:, i) > 0));
      flag = isempty(I);
      if (flag ~= 1)
         correl(i) = corr(obs(I,i), ens(I,i), 'Type', 'Spearman');
      else
         correl(i) = par.mv;
      end
   end

return

end

