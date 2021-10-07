function f = one_sided_exp_decay(t)
% h(t) = e^-t u(t)
% TODO: add parameters for shift, decay rate, perhaps reversal

f = zeros(size(t), 'like', t);
r1 = t > 0;
f(r1) = exp(-t(r1));
