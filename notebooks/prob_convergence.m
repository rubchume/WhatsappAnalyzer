function [objective] = prob_convergence(A_values, p)

N = length(p);

aux = ones(N, 1) * (1:N);
xind = aux(:);
yind = reshape(aux', [N^2,1]);

diagonal = xind ~= yind;
xind = xind(diagonal);
yind = yind(diagonal);

non_diagonal = sub2ind([N, N], xind, yind);

A = zeros(N);
A(non_diagonal) = A_values;

objective = norm(A*p - p);

end

