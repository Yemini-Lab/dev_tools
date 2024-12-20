import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation


def visualize_neurons(nwb_obj):
    target_neurons = ['AWAL', 'I2L', 'AVAL', 'AVBL', 'AWAR', 'I2R', 'AVAR', 'AVBR', 'VB2']
    neurons = nwb_obj.processing['NeuroPAL']['NeuroPALSegmentation']['NeuroPALNeurons']
    neuron_positions = np.asarray(neurons.voxel_mask)  # ensure it's a NumPy array
    neuron_labels = neurons.ID_labels

    coords = []
    for i in range(neuron_labels.shape[0]):
        # Use a condition to ensure a boolean array
        inds = np.argwhere(neuron_positions[..., i] > 0)
        if inds.size == 0:
            coords.append((np.nan, np.nan))
        else:
            mean_pos = inds.mean(axis=0)
            # mean_pos = [x_mean, y_mean, z_mean], so reorder for (y, x)
            coords.append((mean_pos[1], mean_pos[0]))

    coords = np.array(coords)
    rgb_img = generate_mip(nwb_obj)

    plt.imshow(rgb_img, origin='lower', alpha=0.5)
    plt.scatter(coords[:, 0], coords[:, 1], c='red', s=10)

    for i, label in enumerate(neuron_labels):
        if label in target_neurons:
            x, y = coords[i]
            if not np.isnan(x) and not np.isnan(y):
                plt.text(x+5, y+5, label, color='white', fontsize=8,
                         bbox=dict(facecolor='black', alpha=0.5))

    plt.title(f"Neurons: {nwb_obj.subject.subject_id}")
    plt.axis('off')
    plt.show()


def visualize_track(nwb_obj):
    neurons = nwb_obj.processing['CalciumActivity']['TrackedNeurons']['TrackedNeuronROIs']
    neuron_positions = neurons.voxel_mask  # [x, y, z, t]
    neuron_labels = neurons.TrackedNeuronIDs

def generate_mip(nwb_obj):
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

    return rgb_img


def visualize_worm(nwb_obj):
    rgb_img = generate_mip(nwb_obj)
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
    import matplotlib.pyplot as plt
    import numpy as np

    target_neurons = ['AWAL', 'I2L', 'AVAL', 'AVBL', 'AWAR', 'I2R', 'AVAR', 'AVBR', 'VB2']
    activity_module = nwb_obj.processing['CalciumActivity']['ActivityTraces']
    activity_dict = {}
    for n, neuron_name in enumerate(activity_module.neuron):
        if neuron_name in target_neurons:
            activity_dict[neuron_name] = activity_module.activity[n]

    # Compute global y-limits
    if activity_dict:
        activity_values = list(activity_dict.values())
        all_vals = np.concatenate(activity_values)
        all_vals = [x for x in all_vals if not np.isnan(x)]
        ymin, ymax = 0, np.max(all_vals)
    else:
        ymin, ymax = 0, 1

    fig, axs = plt.subplots(3, 3, figsize=(10, 10), sharex=True, sharey=True)
    axs = axs.flatten()

    for i, neuron in enumerate(target_neurons):
        ax = axs[i]
        if neuron in activity_dict:
            ax.plot(activity_dict[neuron])
            ax.set_title(neuron)
            ax.set_ylim(ymin, ymax)
        else:
            ax.set_facecolor("lightgrey")
            ax.text(0.5, 0.5, "No activity found",
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax.transAxes, color='black')
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title(f"{neuron} Activity")

    # Remove unused subplots if any
    for j in range(len(target_neurons), len(axs)):
        axs[j].axis('off')

    # Set shared labels
    fig.text(0.5, 0.04, 'Frame', ha='center')
    fig.text(0.04, 0.5, 'Fluorescence', va='center', rotation='vertical')

    plt.tight_layout(rect=[0.06, 0.06, 1, 1])
    plt.show()
