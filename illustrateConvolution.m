% Create video file to illustrate convolution of rectangular pulse with causal exponential decay.

% Eric Durant <eric.durant@gmail.com> <https://durant.io/>
% Heavily updated version (see git log) of
% https://commons.wikimedia.org/wiki/File:Convolution_of_spiky_function_with_box2.gif

% TODO:
% Support other functions (function calculation objects) / time supports
% Option to disable video generation when live render is all that is needed (saves huge amount of RAM)
% Better handling if size larger than primary monitor is selected (currently size mismatch error)

function illustrateConvolution()

basename = "conv_box_spike";

set(0, 'DefaultAxesFontSize', 15)
set(0, 'DefaultLineLineWidth', 1.0)

dt = 0.001;
t = -2.1 : dt : 4;

if true % original functions
    vals_x = exp(-t);
    vals_x(t<0) = 0;
    vals_h = abs(t)<=0.5;
else % another set of functions to try. This works but updates needed to get less time truncation and moving folding further away from caller.
    % x is a triangular pulse from 0 to 2 s...
    vals_x = zeros(size(t));
    r1 = 0<=t & t<=1;
    vals_x(r1) = t(r1);
    r2 = 1<=t & t<=2;
    vals_x(r2) = 2-t(r2);
    % h(t) = e^-t u(t), but func_h = e^t u(-t) (the *time-reversed* impulse response)
    vals_h = zeros(size(t));
    r3 = t<=0;
    vals_h(r3) = exp(t(r3));
end

fig = figure; % New figure ensures it is on top so the animation is visible during rendering.
width = 1920; % Appropriate GIF rendering size (HD video)
height = 1080;
fig.Position = [1 1 width height]; % LL of primary monitor; doesn't avoid GUI at bottom (e.g., Windows interface).

[~, zero_offset] = min(abs(t));

frameRate = 20.3366666; % Samples of t between rendering video frames (video display rate is separate)
frameCount = floor((t(end)-t(1))/dt / frameRate) + 1; % we only need frame if we reach end of frame; +1 for edges in discrete count
syncFrames = round(frameRate*(0:round(frameCount)))+1; % indexes in t where a frame is rendered; 1 extra since we need to check if we've reached next sync in terminal dropped frames
frame_anim = zeros(height, width, 3, frameCount, 'uint8'); % HWCN, alloc

frame = 1;
integral = nan(size(t));
for offset_i = 1:length(t)
    offset = t(offset_i);
    vals_h_shifted = shift(vals_h, offset_i-zero_offset);
    product = vals_h_shifted.*vals_x;
    integral(offset_i) = sum(product)/length(t)*(t(end)-t(1));

    if offset_i==syncFrames(frame)
        area(t, product, 'facecolor', 'yellow');
        hold on
        plot(t, vals_x, 'b', t, vals_h_shifted, 'r', t, integral, 'k', [offset offset], [0 2], 'k:')
        hold off
        axis image
        axis([-1.6 3.1 0 1.1])
        xlabel('\tau and t')
        grid on
        legend('Area under x(\tau)h(t-\tau)', 'x(\tau)', 'h(t-\tau)', '(x\asth)(t)')
        frame_anim(:,:,:,frame) = frame2im(getframe(gcf));
        frame = frame+1;
    end
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
