% q = stdTNcirc(array, mv)
% Calculates the std of 'array', discounting elements of 'mv'
% Revised: LDM + BN Nov 2011
% - Bug fix: standard deviation returned was in radians
%            should have been in degrees. Fixed.
function q = stdTNcirc(array, mv, var_set, isCircular)

% Initial values
    rad2deg = pi/180;
    b = 0.1547;  % 2/sqrt(3) - 1
    sz = size(array);
    T = sz(1);

    if(nargin == 1)
        mv = [];
    end
    
% Calculations
    deletions = zeros(T, 1);
    counter = 1;
    for t = 1:T
        if(isfinite(find(array(t, :) == mv)))
            deletions(counter) = t;
            counter = counter + 1;
        end
    end
    
    deletions = deletions(1:counter-1);
    array(deletions, :) = [];
    if (length(array) == 0)
       q(1:length(var_set)) = mv;
    else
       for v = 1:length(var_set)
           if (isCircular(var_set(v)))

               % Convert to radians
               dir_rad = array(:, v).*rad2deg;

               % Calculate sum of sines and cosines
               s = mean(sin(dir_rad));
               c = mean(cos(dir_rad));

               % Yamartino estimator
               e = sqrt(1.0 - (s^2 + c^2));

               % Standard deviation
               q(v) = asin(e)*(1 + b*e^3);
               q(v) = q(v)/rad2deg;
           else
               q(v) = std(array(:, v));
           end
       end
    end

return
