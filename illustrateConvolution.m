% Create an animated GIF to illustrate convolution of rectangular pulse
% with causal exponential decay.

% Eric Durant <eric.durant@gmail.com> <https://durant.io/>
% Heavily modified version (MATLAB 2021b updates, pure MATLAB implementation, and more) of
% https://commons.wikimedia.org/wiki/File:Convolution_of_spiky_function_with_box2.gif
% fetched on 2021-10-04

% TODO:
% Add option to live render in MATLAB (and disable GIF generation)
% Fix colormap changing each frame
% Increase rendering resolution
% Change function notation to standard EE signals notation (and MSOE EE3032)
% Support other functions / time supports

function illustrateConvolution()

fileName = "conv_box_spike"+".gif";

t = -2.1 : 0.001 : 4;
F1 = exp(-t);
F1(t<0) = 0;
F2 = abs(t)<=0.5;
clf

[~, zero_offset] = min(abs(t));

frameRate = 20.3366666; % hard-coded constant without explanation in original
SyncFrames = [1 round(frameRate*(1:length(t)))];
frame = 1;
integral = nan(size(t));
for offset_i = 1:length(t)
    offset = t(offset_i);
    shift = offset_i-zero_offset;
    F2_shifted = circshift(F2, [0 shift]);
    product = F2_shifted.*F1;
    integral(offset_i) = sum(product)/length(t)*(t(end)-t(1));

    if offset_i==SyncFrames(frame)
        frame = frame+1;
        area(t, product, 'facecolor', 'yellow');
        hold on
        plot(t, F1, 'b', t, F2_shifted, 'r', t, integral, 'k', [offset offset], [0 2], 'k:')
        hold off
        axis image
        axis([-1.6 3.1 0 1.1])
        xlabel('\tau & t')
        grid on
        legend('Area under f(\tau)g(t-\tau)', 'f(\tau)', 'g(t-\tau)', '(f\astg)(t)')
        [frame_image, cmap] = rgb2ind(frame2im(getframe(gcf)), 256);

        % FIXME: This assumes cmap never changes, which is invalid. Improvements options: 1) pass
        % cmap back to rgb2ind on successive calls to dither to initial map, 2) use a fixed
        % standard map, 3) compute a globally optimal map post hoc. Note: MATLAB R2021b
        % documentation shows support for GIF frame append with cmap varying, but this causes a
        % runtime error that is substantiated on recent MathWorks and reddit posts.

        if frame == 1
            [H,W] = size(frame_image);
            frame_anim = NaN(H,W,1,length(SyncFrames)); % 2021b imwrite GIF requires HWCN or HW, not HWN
        end
        frame_anim(:,:,1,frame) = frame_image;
    end
end

imwrite(frame_anim, cmap, fileName, 'gif', 'Loopcount', inf, 'DelayTime', 1/frameRate)

end % function
