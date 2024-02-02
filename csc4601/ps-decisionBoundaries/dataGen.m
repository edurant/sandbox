% Generate CSV data sets to demonstrate decision boundaries in CSC4601
% Week 3

%% Set 1: Requires quadratic
N = 200;
x1 = unifrnd(-5, 10, [N 1]);
x2 = unifrnd(-10, 10, [N 1]);
% Equation of parabola passing through points (-5, -5), (5,5) and (10, -5)
% x2 = -x1^2/5 + x1 + 5 (assuming rotation angle 0°)
label = x2 < -x1.^2/5 + x1 + 5;

plot(x1(label), x2(label), 'rx', ...
     x1(~label), x2(~label), 'bo')

tbl = table(x1, x2, label);
writetable(tbl, "quad.csv")

%% Set 2: Circle boundary
% Set 1, radius [1, 2]
% Set 2, radius [3, 4]
N = 50;
cplx = exp(1j*unifrnd(-pi, pi, [2*N 1])) .* [unifrnd(1, 2, [N 1]); unifrnd(3, 4, [N 1])];
x1 = real(cplx);
x2 = imag(cplx);
label = [false(N,1); true(N,1)];
plot(x1(label), x2(label), 'rx', ...
     x1(~label), x2(~label), 'bo')

tbl = table(x1, x2, label);
writetable(tbl, "circle.csv")
