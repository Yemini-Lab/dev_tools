import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import ConnectionPatch


def visualize_neurons(nwb_obj):
    target_neurons = ['AWAL', 'I2L', 'AVAL', 'AVBL', 'AWAR', 'I2R', 'AVAR', 'AVBR', 'VB2']
    neurons = nwb_obj.processing['NeuroPAL']['NeuroPALSegmentation']['NeuroPALNeurons']

    neuron_positions = np.array(neurons.voxel_mask[:].tolist())
    neuron_labels = np.array(neurons.ID_labels)
    rgb_img = generate_mip(nwb_obj)

    # Extract just x and y
    x_coords = neuron_positions[:, 0]
    y_coords = neuron_positions[:, 1]

    # Filter for target neurons
    mask = np.isin(neuron_labels, target_neurons)
    target_positions = neuron_positions[mask, :2]  # Ensure only x, y are taken
    target_labels = neuron_labels[mask]

    # Sort targets by y coordinate
    sorted_indices = np.argsort(target_positions[:, 1])
    target_positions = target_positions[sorted_indices]
    target_labels = target_labels[sorted_indices]

    plt.imshow(rgb_img, origin='lower', alpha=0.8)
    plt.scatter(x_coords, y_coords, facecolors='none', edgecolors='w', s=20, alpha=0.5)

    # Determine left label column x position
    label_x = x_coords.min() - 100

    # Evenly space labels vertically
    diff = target_positions[-1, 1] - target_positions[0, 1]
    expanded_diff = diff * 2  # Increase spacing by factor of 2
    label_ys = np.linspace(target_positions[0, 1], target_positions[0, 1] + expanded_diff, len(target_positions))

    # Draw labels and connecting lines
    for i in range(len(target_positions)):
        tx, ty = target_positions[i]
        lbl = target_labels[i]
        ly = label_ys[i]

        plt.text(label_x, ly, lbl, color='white', fontsize=8,
                 bbox=dict(facecolor='black', alpha=0.3),
                 ha='right', va='center')
        con = ConnectionPatch(xyA=(label_x, ly), xyB=(tx, ty),
                              coordsA='data', coordsB='data',
                              arrowstyle='-', color='yellow', linewidth=1)
        plt.gca().add_artist(con)

    plt.title(f"{nwb_obj.subject.subject_id} Neurons ({len(neuron_labels)})")
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
