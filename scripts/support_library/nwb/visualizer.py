import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation


def visualize_worm(nwb_obj):
    color_stack = nwb_obj.acquisition['NeuroPALImageRaw'].data[:]
    rgbw_indices = nwb_obj.acquisition['NeuroPALImageRaw'].RGBW_channels[:] - 1
    channel_gammas = nwb_obj.processing['NeuroPAL']['NeuroPAL_ID'].gammas[:]

    if color_stack.ndim < 4:
        print("Data format not as expected.")
        return

    # Max intensity projection over z
    max_img = color_stack.max(axis=1)  # shape: (c, x, y)

    rgb_img = np.zeros((max_img.shape[2], max_img.shape[1], 3), dtype=float)
    for i, chan_idx in enumerate(rgbw_indices[:3]):
        gamma = channel_gammas[chan_idx]
        channel_data = max_img[chan_idx, ...].astype(float)
        # Normalize channel to [0,1]
        max_val = channel_data.max() if channel_data.max() != 0 else 1
        channel_data /= max_val
        # Apply gamma correction
        channel_data = np.power(channel_data, 1.0 / gamma)
        # Scale back
        channel_data *= max_val
        rgb_img[..., i] = channel_data.T

    plt.imshow(rgb_img, origin='lower')
    plt.title(f"Worm visualization: {nwb_obj.subject.subject_id}")
    plt.axis('off')

    subject_info = []
    if getattr(nwb_obj, 'subject', None) is not None:
        for attr in ['subject_id', 'age', 'description', 'genotype', 'sex', 'species', 'strain']:
            val = getattr(nwb_obj.subject, attr, None)
            if val is not None:
                subject_info.append(f"{attr.capitalize()}: {val}")

    if subject_info:
        plt.text(1.05, 0.5, "\n".join(subject_info), transform=plt.gca().transAxes,
                 verticalalignment='center', fontsize=10)

    plt.show()


def visualize_video(nwb_obj):
    video_array = nwb_obj.acquisition['CalciumImageSeries'].data[1:75, :, :, :, :]

    if video_array.ndim < 5:
        print("Data format not as expected.")
        return

    max_projection = video_array.max(axis=3)
    num_frames = min(75, max_projection.shape[0])

    fig, ax = plt.subplots()
    rgb_frame = np.zeros((max_projection.shape[2], max_projection.shape[1], 3), dtype=video_array.dtype)
    for i, chan_idx in enumerate([0, 1, 2]):
        rgb_frame[..., i] = max_projection[0, :, :, chan_idx].T

    im = ax.imshow(rgb_frame, origin='lower')
    ax.axis('off')

    def update(frame_idx):
        for i, chan_idx in enumerate([0, 1, 2]):
            rgb_frame[..., i] = max_projection[frame_idx, :, :, chan_idx].T
        im.set_data(rgb_frame)
        ax.set_title(f"Frame {frame_idx}", loc='left')
        return [im]

    ani = animation.FuncAnimation(fig, update, frames=num_frames, interval=100, blit=True)

    ff_writer = animation.FFMpegWriter(fps=10)
    filename = f"{nwb_obj.subject.subject_id}_20241220_test.mp4"
    ani.save(filename=filename, writer=ff_writer)

    plt.show()


def visualize_activity(nwb_obj):
    target_neurons = ['AWA', 'I2', 'AVA', 'AVB', 'VB2']
    activity_module = nwb_obj.processing['CalciumActivity']['ActivityTraces']
    activity_dict = {}
    for n in range(len(activity_module.neuron)):
        neuron_name = activity_module.neuron[n]
        if neuron_name in target_neurons:
            activity_dict[neuron_name] = activity_module.activity[n]
    if len(activity_dict) == 0:
        print("No target neurons found.")
        return
    plt.figure()
    for neuron, trace in activity_dict.items():
        plt.plot(trace, label=neuron)
    plt.legend()
    plt.title("Calcium activity of selected neurons")
    plt.xlabel("Time")
    plt.ylabel("Fluorescence signal")
    plt.show()
