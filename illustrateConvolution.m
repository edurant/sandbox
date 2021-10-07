% Create an animated GIF to illustrate convolution of rectangular pulse
% with causal exponential decay.

% Eric Durant <eric.durant@gmail.com> <https://durant.io/>
% Heavily updated version (see git log) of
% https://commons.wikimedia.org/wiki/File:Convolution_of_spiky_function_with_box2.gif

% TODO:
% Option to disable GIF generation (when live render is all that is needed)
% Support other functions / time supports
% Try GIF without dither
% Increase GIF render RAM efficiency (about 6 GB peak, rendering raw 24b video to RAM)
% Increase GIF efficiency/compression/cmap depth (32 MB GIF typical render)
% Better handling if size larger than primary monitor is selected (currently size mismatch error)

function illustrateConvolution()

fileName = "conv_box_spike"+".gif";

dt = 0.001;
t = -2.1 : dt : 4;
func_x = exp(-t);
func_x(t<0) = 0;
func_h = abs(t)<=0.5;

fig = figure; % New figure ensures it is on top so the animation is visible during rendering.
width = 1920; % Appropriate GIF rendering size (HD video)
height = 1080;
width = 1024;
height = 768;
fig.Position = [1 1 width height]; % LL of primary monitor; doesn't avoid GUI at bottom (e.g., Windows interface).
% Doesn't check that (scaled) monitor is large enough)

[~, zero_offset] = min(abs(t));

frameRate = 20.3366666; % Samples of t before a video frame is rendered (video display rate is separate)
frameCount = floor((t(end)-t(1))/dt / frameRate) + 1; % we only need frame if we reach end of frame; +1 for edges in discrete count
SyncFrames = round(frameRate*(0:round(frameCount)))+1; % indexes in t where a frame is rendered; 1 extra since we need to check if we've reached next sync in terminal dropped frames
frame_anim = zeros(height, width, 3, frameCount, 'uint8'); % HWCN, alloc

frame = 1;
integral = nan(size(t));
for offset_i = 1:length(t)
    offset = t(offset_i);
    shift = offset_i-zero_offset;
    func_h_shifted = circshift(func_h, [0 shift]);
    product = func_h_shifted.*func_x;
    integral(offset_i) = sum(product)/length(t)*(t(end)-t(1));

    if offset_i==SyncFrames(frame)
        area(t, product, 'facecolor', 'yellow');
        hold on
        plot(t, func_x, 'b', t, func_h_shifted, 'r', t, integral, 'k', [offset offset], [0 2], 'k:')
        hold off
        axis image
        axis([-1.6 3.1 0 1.1])
        xlabel('\tau & t')
        grid on
        legend('Area under x(\tau)h(t-\tau)', 'x(\tau)', 'h(t-\tau)', '(x\asth)(t)')
        frame_anim(:,:,:,frame) = frame2im(getframe(gcf));
        frame = frame+1;
    end
end

frame_anim = permute(frame_anim, [1 2 4 3]);
sz = size(frame_anim); % HWNC
[frame_anim_idx, cmap] = rgb2ind(reshape(frame_anim, sz(1), [], 3), 256); % collapse (WN) for rgb2ind
sz(4) = 1; % C = 1
frame_anim_idx = permute(reshape(frame_anim_idx, sz), [1 2 4 3]); % H(WN)C -> HWNC -> HWCN

imwrite(frame_anim_idx, cmap, fileName, 'gif', 'Loopcount', inf, 'DelayTime', 1/frameRate) % TODO: reasonable frameRate, but based on function dt, not display rate, see definition.

end % function
