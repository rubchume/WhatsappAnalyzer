A = [0, 0.25, 0.75; 2/3, 0, 1/3; 2/5, 3/5, 0]';
[Q, P] = eig(A);
eigenvalues = diag(P);
[~, ind_sort] = sort(eigenvalues, 'descend');
P = diag(eigenvalues(ind_sort));
Q = Q(:, ind_sort);
q_1 = Q(:, 1);

p = [1, 0, 0]';
c = Q\p;

q_1*c(1)

A^1000*p

inv(Q)

Q'*Q

%% Modificaciones
Q

Qmod = Q;
Qmod(:, 2) = [1, -0.25, -0.75]';
Amod = Qmod*P/Qmod;

Q*P/Q
Amod^1000
A^1000 * q_1/sum(q_1)

%% Find eigenvectors from p

p = [0.5, 0.4, 0.1]';
onesvec = [1, 1, 1]'/norm([1, 1, 1]);

q1 = p/norm(p);

q2 = q1 - dot(onesvec, q1)*onesvec;
q2 = q2/norm(q2);

qrest = null([1, 1, 1; q2']);

Q = [q1, q2, qrest];

Q'*Q

eigvalrest = -Q(:, 2:3).*(Q(:, 2:3) - ones(3,1)*q1'*Q(:, 2:3)/sum(q1)) \ (q1/sum(q1));
P = diag([1; eigvalrest]);

A = Q*P/Q

A^100

%%
N = 1e7;
p = [0.4, 0.3, 0.2, 0.1];

sequence = sum(rand([N, 1]) > cumsum(p), 2) + 1;
mean(sequence(1:end-1) == 2 & sequence(2:end) == 1)

M = zeros(length(p));
for i = 1:length(p)
    for j = 1:length(p)
        M(i, j) = mean(sequence(1:end-1) == j & sequence(2:end) == i);
    end
end

disp("hola")
sum(M(1, [2, 3, 4]))
sum(M(2, [1, 3, 4]))
sum(M(3, [1, 2, 4]))
sum(M(4, [1, 2, 3]))

%% Optimization 1

p_empirical = [0.4, 0.3, 0.2, 0.1]';
Aeq = [1, 1, 1, 1];
beq = 1;

func2 = @(p) prob_convergence2(p, p_empirical);
p_estimated = fmincon(func2, p_empirical, [], [], Aeq, beq);

M = p_estimated*p_estimated';

p_emp = zeros(4,1);
p_emp(1) = sum(M(1, [2, 3, 4]));
p_emp(2) = sum(M(2, [1, 3, 4]));
p_emp(3) = sum(M(3, [1, 2, 4]));
p_emp(4) = sum(M(4, [1, 2, 3]));

p_emp/sum(p_emp)

non_diagonal_probabilities = (1 - eye(4)).*M;
non_diagonal_probabilities_normalized = non_diagonal_probabilities / sum(sum(non_diagonal_probabilities));

M_no_repeat = non_diagonal_probabilities ./ sum(non_diagonal_probabilities)

