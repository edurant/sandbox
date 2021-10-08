fh = @one_sided_exp_decay;
fx = @triangular_pulse;

ct = [-3.5 4.1];
pt = [-0.5 4.0];

illustrateConvolution(fh, fx, ct, pt)
% Call with no arguments to use original Wikipedia h(t) and x(t).
