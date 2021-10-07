% Create video file to illustrate convolution of rectangular pulse with causal exponential decay.

% Eric Durant <eric.durant@gmail.com> <https://durant.io/>
% Heavily updated version (see git log) of
% https://commons.wikimedia.org/wiki/File:Convolution_of_spiky_function_with_box2.gif

% TODO:
% Support other functions / time supports
% Option to disable video generation when live render is all that is needed (saves huge amount of RAM)
% Better handling if size larger than primary monitor is selected (currently size mismatch error)

function illustrateConvolution()

basename = "conv_box_spike";

set(0, 'DefaultAxesFontSize', 15)
set(0, 'DefaultLineLineWidth', 1.0)

dt = 0.001;
t = -2.1 : dt : 4;
func_x = exp(-t);
func_x(t<0) = 0;
func_h = abs(t)<=0.5;

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
    shift = offset_i-zero_offset;
    func_h_shifted = circshift(func_h, [0 shift]);
    product = func_h_shifted.*func_x;
    integral(offset_i) = sum(product)/length(t)*(t(end)-t(1));

    if offset_i==syncFrames(frame)
        area(t, product, 'facecolor', 'yellow');
        hold on
        plot(t, func_x, 'b', t, func_h_shifted, 'r', t, integral, 'k', [offset offset], [0 2], 'k:')
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
