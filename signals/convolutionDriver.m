fh = @one_sided_exp_decay;
fx = @triangular_pulse;

% TODO: illustrateConvolution should scale appropriately beyond [0,1]
% fh = @(t)(3*fh(t)); % scale vertically by 3
% fx = @(t)(2*fx(t)); % scale vertically by 2

ct = [-3.5 4.1];
pt = [-0.5 4.0];
vt = [-0.5 4.1];

illustrateConvolution(fh, fx, ct, pt, vt)
% Call with no arguments to use original Wikipedia h(t) and x(t).
