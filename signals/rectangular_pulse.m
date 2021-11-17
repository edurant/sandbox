function f = rectangular_pulse(t, t0)
% rectangular pulse: 1 on [t0(1), t0(2)] (default: [-1/2, 1/2])
% t0 should be ascending else pulse is never active

narginchk(1,2)
if nargin==1, t0 = [-1/2 1/2]; end
assert(isvector(t0) && numel(t0)==2)

f = zeros(size(t), 'like', t);
f(t0(1) <= t & t <= t0(2)) = 1;
