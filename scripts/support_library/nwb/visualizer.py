import matplotlib.pyplot as plt
import numpy as np

def visualize_worm(nwb_obj):
    # Dimensions: (c, z, x, y)
    color_stack = nwb_obj.acquisition['NeuroPALImageRaw'].data[:]
    rgbw_indices = nwb_obj.acquisition['NeuroPALImageRaw'].RGBW_channels[:]

    if color_stack.ndim < 4:
        print("Data format not as expected.")
        return

    # Choose a middle z-plane
    z_idx = color_stack.shape[1] // 2
    # Extract that plane: shape is (c, x, y)
    slice_img = color_stack[:, z_idx, :, :]

    # Create an RGB image: (x, y, 3)
    rgb_img = np.zeros((slice_img.shape[1], slice_img.shape[2], 3), dtype=slice_img.dtype)
    for i, chan_idx in enumerate(rgbw_indices[:3]):
        rgb_img[..., i] = slice_img[chan_idx, ...]

    plt.imshow(rgb_img, origin='lower')
    plt.title(f"Worm visualization: {nwb_obj.subject.subject_id}")
    plt.axis('off')
    plt.show()


def visualize_video(nwb_obj):
    # Dimensions: (t, x, y, z, c)
    video_array = nwb_obj.acquisition['CalciumImageSeries'].data[:]

    if video_array.ndim < 5:
        print("Data format not as expected.")
        return

    frame_idx = 0
    # Choose a middle z-plane
    z_idx = video_array.shape[3] // 2
    # Create an RGB frame: (x, y, 3)
    rgb_frame = np.zeros((video_array.shape[1], video_array.shape[2], 3), dtype=video_array.dtype)
    for i, chan_idx in enumerate([1, 2, 3]):
        rgb_frame[..., i] = video_array[frame_idx, :, :, z_idx, chan_idx]

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
