function [output] = prob_convergence2(p, p_empirical)

output = norm(p_empirical - (p - p.^2) / sum(p - p.^2));

end

