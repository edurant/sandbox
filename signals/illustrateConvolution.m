% Create video file to illustrate convolution of 2 given functions.

% Eric Durant <eric.durant@gmail.com> <https://durant.io/>
% Heavily updated version (see git log) of
% https://commons.wikimedia.org/wiki/File:Convolution_of_spiky_function_with_box2.gif

% TODO:
% Add areas and demonstrate area property
% Better handling if size larger than primary monitor is selected (currently size mismatch error)

function illustrateConvolution(fh, fx, ct, pt, vt)
% fh, fx: function handles taking t of any shape and returning corresponding function values
% ct, pt, vt: ordered, 2-element time range vectors.
% 1. ct: calculation time range. x(tau), h(-tau), and y(t) are calculated on this
%    range and assumed to be 0 outside of this range.
%    Also, the animation runs over this range sweeping t in h(t-tau).
% 2. pt: plotting time range, typically a subset of ct.
% 3. vt: video time range, typically a subset of ct and often a superset of pt
%
% This system will require some compromises depending on the particular
% signals used. Additional capabilities could be added.

narginchk(0,5)
assert (nargin ~= 1, "if h(t) is provided, x(t) must also be provided.")

set(0, 'DefaultAxesFontSize', 15, ...
       'DefaultLineLineWidth', 1.0)

if ~exist('ct', 'var'), ct = [-2.1 4.0]; end
if ~exist('pt', 'var'), pt = [-1.6 3.1]; end
assert(numel(ct)==2), assert(diff(ct)>0)
assert(numel(pt)==2), assert(diff(pt)>0)
if ~exist('vt', 'var'), vt = pt; end
assert(numel(vt)==2), assert(diff(vt)>0)

dt = 0.001;
t = ct(1) : dt : ct(2);

if ~exist('fx', 'var')
    vals_x = exp(-t); % causal exponential decay
    vals_x(t<0) = 0;
    vals_h = abs(t)<=0.5; % rectangular pulse
else
    vals_x = fx(t); % x(tau)
    vals_h = fh(-t); % h(t-tau), t=0 case; shifts happen below
end

ylim_max = max([max(vals_x), max(vals_h), max(vals_x)*max(vals_h)])*1.1;
% TODO: consider max area, consider outliers

fig = figure; % New figure ensures it is on top so the animation is visible during rendering.
width = 1920; % Appropriate GIF rendering size (HD video)
height = 1080;
fig.Position = [1 1 width height]; % LL of primary monitor; doesn't avoid GUI at bottom (e.g., Windows interface).

[~, zero_offset] = min(abs(t));

frameRate = 10.1; % Samples of t between rendering video frames (video display rate is separate)

vw = VideoWriter("conv", "MPEG-4");
vw.FrameRate = 60;
open(vw)

accumulatedFrames = frameRate; % initialize so that initial frame in vt is rendered
integral = nan(size(t));
for offset_i = 1:length(t)
    offset = t(offset_i);
    vals_h_shifted = shift(vals_h, offset_i-zero_offset);
    product = vals_h_shifted.*vals_x;
    integral(offset_i) = sum(product)/length(t)*(diff(ct));

    if vt(1) <= offset && offset <= vt(2)
        if accumulatedFrames + 0.5 >= frameRate % emit a frame
            accumulatedFrames = accumulatedFrames - frameRate;
            area(t, product, 'facecolor', 'yellow');
            hold on
            plot(t, vals_x, 'b', t, vals_h_shifted, 'r', t, integral, 'k', [offset offset], [0 2], 'k:')
            hold off
            axis image
            axis([pt(1) pt(2) 0 ylim_max])
            xlabel('\tau and t')
            grid on
            legend('Area under x(\tau)h(t-\tau)', 'x(\tau)', 'h(t-\tau)', '(x\asth)(t)')
            writeVideo(vw, frame2im(getframe(gcf)))
        end
        accumulatedFrames = accumulatedFrames + 1;
    end
end

close(vw)

end % function

function vec = shift(vec, offset)
% Shifts a 1-D vector by offset places; pads with 0.
assert(max(size(vec))==numel(vec), 'vec must be a 1-D vector (with any number of singleton dimensions)')
if abs(offset) > length(vec)
    vec = zeros(size(vec),'like',vec);
elseif offset==0
    return
else
    if offset>0
        result = [zeros(1,offset,'like',vec) vec(1:end-offset)];
    else
        result = [vec(1-offset:end) zeros(1,-offset,'like',vec)];
    end
    vec = reshape(result,size(vec));
end
end % function
