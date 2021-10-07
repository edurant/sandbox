function f = triangular_pulse(t)
% triangular pulse: (0,0) -> (1,1) -> (2,0)
% TODO: add parameters for pulse width, height, center, etc.

f = zeros(size(t), 'like', t);
r1 = 0<=t & t<=1;
f(r1) = t(r1);
r2 = 1<=t & t<=2;
f(r2) = 2-t(r2);
