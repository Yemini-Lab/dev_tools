import matplotlib.pyplot as plt
import numpy as np


def visualize_worm(nwb_obj):
    color_stack = nwb_obj.acquisition['NeuroPALImageRaw'].data[:]
    rgbw_indices = nwb_obj.acquisition['NeuroPALImageRaw'].RGBW_channels[:]
    channel_gammas = nwb_obj.processing['NeuroPAL']['NeuroPAL_ID'].gammas[:]

    if color_stack.ndim < 4:
        print("Data format not as expected.")
        return

    # Max intensity projection over z
    max_img = color_stack.max(axis=1)  # shape: (c, x, y)

    rgb_img = np.zeros((max_img.shape[2], max_img.shape[1], 3), dtype=max_img.dtype)
    for i, chan_idx in enumerate(rgbw_indices[:3]):
        gamma = channel_gammas[chan_idx]
        corrected = np.power(max_img[chan_idx, ...], 1 / gamma)
        rgb_img[..., i] = corrected.T

    plt.imshow(rgb_img, origin='lower')
    plt.title(f"Worm visualization: {nwb_obj.subject.subject_id}")
    plt.axis('off')

    # Add subject info to the right of the image
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
    # Dimensions: (t, x, y, z, c)
    video_array = nwb_obj.acquisition['CalciumImageSeries'].data[:]

    if video_array.ndim < 5:
        print("Data format not as expected.")
        return

    # Max intensity projection over z
    max_projection = video_array.max(axis=3)  # (t, x, y, c)

    frame_idx = 0
    # Create an RGB frame: (y, x, 3)
    rgb_frame = np.zeros((max_projection.shape[2], max_projection.shape[1], 3), dtype=video_array.dtype)
    for i, chan_idx in enumerate([1, 2, 3]):
        # Transpose to (y, x)
        rgb_frame[..., i] = max_projection[frame_idx, :, :, chan_idx].T

    plt.imshow(rgb_frame, origin='lower')
    plt.title("Video frame 0")
    plt.axis('off')
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
    plt.ylabel("Activity")
    plt.show()
