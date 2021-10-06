% Create an animated GIF to illustrate convolution of rectangular pulse
% with causal exponential decay.

% Eric Durant <eric.durant@gmail.com> <https://durant.io/>
% Heavily updated version (see git log) of
% https://commons.wikimedia.org/wiki/File:Convolution_of_spiky_function_with_box2.gif

% TODO:
% Option to disable GIF generation (when live render is all that is needed)
% Change function notation to standard EE signals notation (and MSOE EE3032)
% Support other functions / time supports
% Increase GIF render RAM efficiency (about 6 GB peak, rendering raw 24b video to RAM)
% Increase GIF efficiency/compression/cmap depth (32 MB GIF typical render)

function illustrateConvolution()

fileName = "conv_box_spike"+".gif";

t = -2.1 : 0.001 : 4;
F1 = exp(-t);
F1(t<0) = 0;
F2 = abs(t)<=0.5;

fig = figure; % New figure ensures it is on top so the animation is visible during rendering.
% TODO: Define width height as variables here, prealloc frame_anim
fig.Position = [1 1 1920 1080]; % LL of primary monitor; doesn't avoid GUI at bottom (e.g., Windows interface).
% Appropriate GIF rendering size (HD video); doesn't check that (scaled) monitor is large enough)

[~, zero_offset] = min(abs(t));

frameRate = 20.3366666; % hard-coded constant without explanation in original
SyncFrames = [1 round(frameRate*(1:length(t)))]; % TODO: This is much longer than needed, which makes using its length for alloc frame_image below wasteful. should it be based on duration of t (not samples of t)?
frame = 1;
integral = nan(size(t));
for offset_i = 1:length(t)
    offset = t(offset_i);
    shift = offset_i-zero_offset;
    F2_shifted = circshift(F2, [0 shift]);
    product = F2_shifted.*F1;
    integral(offset_i) = sum(product)/length(t)*(t(end)-t(1));

    if offset_i==SyncFrames(frame)
        frame = frame+1; % TODO: Bug? frame always >= 2
        area(t, product, 'facecolor', 'yellow');
        hold on
        plot(t, F1, 'b', t, F2_shifted, 'r', t, integral, 'k', [offset offset], [0 2], 'k:')
        hold off
        axis image
        axis([-1.6 3.1 0 1.1])
        xlabel('\tau & t')
        grid on
        legend('Area under f(\tau)g(t-\tau)', 'f(\tau)', 'g(t-\tau)', '(f\astg)(t)')
        frame_image = frame2im(getframe(gcf));
        if frame == 1 % FIXME: This alloc code never runs, frame >= 2; so frame_anim grows dynamically, resulting in noticable alloc pauses in live render
            [H,W] = size(frame_image);
            frame_anim = NaN(H,W,3,length(SyncFrames)); % HWCN
            % FIXME: frame_image is uint8, so can't use NaN
        end
        frame_anim(:,:,:,frame) = frame_image;
    end
end

frame_anim = permute(frame_anim, [1 2 4 3]);
sz = size(frame_anim); % HWNC
[frame_anim_idx, cmap] = rgb2ind(reshape(frame_anim, sz(1), [], 3), 256); % collapse (WN) for rgb2ind
sz(4) = 1; % C = 1
frame_anim_idx = permute(reshape(frame_anim_idx, sz), [1 2 4 3]); % H(WN)C -> HWNC -> HWCN

imwrite(frame_anim_idx, cmap, fileName, 'gif', 'Loopcount', inf, 'DelayTime', 1/frameRate)

end % function
