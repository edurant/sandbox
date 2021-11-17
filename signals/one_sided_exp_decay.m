function f = one_sided_exp_decay(t, a)
% h(t) = e^-(at) u(t)
% TODO: add parameters for shift, perhaps reversal

narginchk(1,2)
if nargin == 1, a = 1; end
assert(isscalar(a))

f = zeros(size(t), 'like', t);
r1 = t > 0;
f(r1) = exp(-a*t(r1));
