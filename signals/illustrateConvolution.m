% Create video file to illustrate convolution of 2 given functions.

% Eric Durant <eric.durant@gmail.com> <https://durant.io/>
% Heavily updated version (see git log) of
% https://commons.wikimedia.org/wiki/File:Convolution_of_spiky_function_with_box2.gif

% TODO:
% Option to start (and maybe stop) video after (before) the calculation extents
% Option to disable video generation when live render is all that is needed (saves huge amount of RAM)
% Better handling if size larger than primary monitor is selected (currently size mismatch error)

function illustrateConvolution(fh, fx, ct, pt)
% fh, fx: function handles taking t of any shape and returning corresponding function values
% ct, pt, ordered, 2-element time support vectors.
% There are 2 time ranges:
% 1. ct: calculation time range. x(tau), h(-tau), and y(t) are calculated on this
%    range and assumed to be 0 outside of this range.
%    Also, the animation runs over this range sweeping t in h(t-tau).
% 2. pt: plotting time range, typically a subset of calculation time range.
%
% This system will require some compromises depending on the particular
% signals used. Additional capabilities could be added.

narginchk(0,4)
assert (nargin ~= 1, "if h(t) is provided, x(t) must also be provided.")

basename = "conv";

set(0, 'DefaultAxesFontSize', 15)
set(0, 'DefaultLineLineWidth', 1.0)

if ~exist('ct', 'var'), ct = [-2.1 4.0]; end
if ~exist('pt', 'var'), pt = [-1.6 3.1]; end
assert(numel(ct)==2), assert(diff(ct)>0)
assert(numel(pt)==2), assert(diff(pt)>0)

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

fig = figure; % New figure ensures it is on top so the animation is visible during rendering.
width = 1920; % Appropriate GIF rendering size (HD video)
height = 1080;
fig.Position = [1 1 width height]; % LL of primary monitor; doesn't avoid GUI at bottom (e.g., Windows interface).

[~, zero_offset] = min(abs(t));

frameRate = 20.3366666; % Samples of t between rendering video frames (video display rate is separate)
frameCount = floor((diff(ct))/dt / frameRate) + 1; % we only need frame if we reach end of frame; +1 for edges in discrete count
frame_anim = zeros(height, width, 3, frameCount, 'uint8'); % HWCN, alloc

frame = 1;
accumulatedFrames = frameRate; % initialize so that initial frame is rendered
integral = nan(size(t));
for offset_i = 1:length(t)
    offset = t(offset_i);
    vals_h_shifted = shift(vals_h, offset_i-zero_offset);
    product = vals_h_shifted.*vals_x;
    integral(offset_i) = sum(product)/length(t)*(diff(ct));

    if accumulatedFrames + 0.5 >= frameRate % emit a frame
        accumulatedFrames = accumulatedFrames - frameRate;
        area(t, product, 'facecolor', 'yellow');
        hold on
        plot(t, vals_x, 'b', t, vals_h_shifted, 'r', t, integral, 'k', [offset offset], [0 2], 'k:')
        hold off
        axis image
        axis([pt(1) pt(2) 0 1.1])
        xlabel('\tau and t')
        grid on
        legend('Area under x(\tau)h(t-\tau)', 'x(\tau)', 'h(t-\tau)', '(x\asth)(t)')
        frame_anim(:,:,:,frame) = frame2im(getframe(gcf));
        frame = frame+1;
    end
    accumulatedFrames = accumulatedFrames + 1;
end

renderMPEG4(frame_anim, basename)
% renderAnimatedGif(frame_anim, basename)

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

function renderAnimatedGif(frame_anim, basename)
% frame_anim must be HWCN
frame_anim = permute(frame_anim, [1 2 4 3]);
sz = size(frame_anim); % HWNC
[frame_anim_idx, cmap] = rgb2ind(reshape(frame_anim, sz(1), [], 3), 256); % collapse (WN) for rgb2ind
sz(4) = 1; % C = 1
frame_anim_idx = permute(reshape(frame_anim_idx, sz), [1 2 4 3]); % H(WN)C -> HWNC -> HWCN
imwrite(frame_anim_idx, cmap, basename+".gif", 'gif', 'Loopcount', inf, 'DelayTime', 1/30)
% 30 Hz is a bit slow, but animated GIFs are already huge
end % function

function renderMPEG4(frame_anim, basename)
v = VideoWriter(basename,'MPEG-4');
open(v)
writeVideo(v, frame_anim)
close(v)
end
