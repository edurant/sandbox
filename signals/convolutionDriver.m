fh = @(t)one_sided_exp_decay(t,2);
fh = @(t)(2*fh(t)); % scale vertically by 2

% fx = @triangular_pulse;
fx = @(t)(1.5*rectangular_pulse(t,[-2 1]));

% calculation, plotting, video
ct = [-4 4.1];
pt = [-4 4];
vt = [-3 3];

illustrateConvolution(fh, fx, ct, pt, vt)
% Call with no arguments to use original Wikipedia h(t) and x(t).
