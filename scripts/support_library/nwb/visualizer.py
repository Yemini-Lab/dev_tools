import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import ConnectionPatch
from datetime import datetime


def plot_worm(ax, nwb_obj):
    rgb_img = generate_mip(nwb_obj)
    ax.imshow(rgb_img, origin='lower')
    ax.set_title(f"Worm visualization: {nwb_obj.subject.subject_id}")
    ax.axis('off')
    subject_info = []
    if getattr(nwb_obj, 'subject', None) is not None:
        for attr in ['subject_id', 'age', 'description', 'genotype', 'sex', 'species', 'strain']:
            val = getattr(nwb_obj.subject, attr, None)
            if val is not None:
                subject_info.append(f"{attr.capitalize()}: {val}")
    if subject_info:
        ax.text(1.05, 0.5, "\n".join(subject_info), transform=ax.transAxes,
                verticalalignment='center', fontsize=10)


def plot_neurons(ax, nwb_obj):
    target_neurons = ['AWAL', 'I2L', 'AVAL', 'AVBL', 'AWAR', 'I2R', 'AVAR', 'AVBR', 'VB2']
    neurons = nwb_obj.processing['NeuroPAL']['NeuroPALSegmentation']['NeuroPALNeurons']
    neuron_positions = np.array(neurons.voxel_mask[:].tolist())
    neuron_labels = np.array(neurons.ID_labels)
    rgb_img = generate_mip(nwb_obj)
    x_coords = neuron_positions[:, 0]
    y_coords = neuron_positions[:, 1]
    mask = np.isin(neuron_labels, target_neurons)
    target_positions = neuron_positions[mask, :2]
    target_labels = neuron_labels[mask]
    sorted_indices = np.argsort(target_positions[:, 1])
    target_positions = target_positions[sorted_indices]
    target_labels = target_labels[sorted_indices]
    ax.imshow(rgb_img, origin='lower')
    ax.scatter(x_coords, y_coords, facecolors='none', edgecolors='w', s=20, alpha=0.6)
    label_x = x_coords.min() - 100
    diff = target_positions[-1, 1] - target_positions[0, 1]
    expanded_diff = diff * 2.5
    label_ys = np.linspace(target_positions[0, 1], target_positions[0, 1] + expanded_diff, len(target_positions))
    vertical_offset = -135
    for i in range(len(target_positions)):
        tx, ty = target_positions[i]
        lbl = target_labels[i]
        ly = label_ys[i] + vertical_offset
        ax.text(label_x, ly, lbl, color='white', fontsize=8, ha='right', va='center')
        con = ConnectionPatch(xyA=(label_x, ly), xyB=(tx, ty),
                              coordsA='data', coordsB='data',
                              arrowstyle='-', color='yellow', linewidth=0.4, alpha=1)
        ax.add_artist(con)
    ax.set_title(f"{nwb_obj.subject.subject_id} Neurons ({len(neuron_labels)})")
    ax.axis('off')


def plot_activity(ax, nwb_obj):
    target_neurons = ['AWAL', 'I2L', 'AVAL', 'AVBL', 'AWAR', 'I2R', 'AVAR', 'AVBR', 'VB2']
    activity_module = nwb_obj.processing['CalciumActivity']['ActivityTraces']
    activity_dict = {}
    for n, neuron_name in enumerate(activity_module.neuron):
        if neuron_name in target_neurons:
            activity_dict[neuron_name] = activity_module.activity[n]
    if activity_dict:
        activity_values = list(activity_dict.values())
        all_vals = np.concatenate(activity_values)
        all_vals = [x for x in all_vals if not np.isnan(x)]
        ymin, ymax = 0, np.max(all_vals)
    else:
        ymin, ymax = 0, 1
    # Create a 3x3 grid within ax
    ax.set_axis_off()
    gs = ax.get_subplotspec().subgridspec(3, 3)
    axs = [ax.figure.add_subplot(gs[i // 3, i % 3]) for i in range(9)]
    for i, neuron in enumerate(target_neurons):
        subax = axs[i]
        if neuron in activity_dict:
            subax.plot(activity_dict[neuron])
            subax.set_title(neuron, fontsize=8)
            subax.set_ylim(ymin, ymax)
            subax.tick_params(axis='both', which='major', labelsize=6)
        else:
            subax.set_facecolor("lightgrey")
            subax.text(0.5, 0.5, "No activity found",
                       horizontalalignment='center', verticalalignment='center',
                       transform=subax.transAxes, color='black', fontsize=6)
            subax.set_xticks([])
            subax.set_yticks([])
            subax.set_title(f"{neuron} Activity", fontsize=8)
    for j in range(len(target_neurons), 9):
        axs[j].axis('off')
    ax.figure.text(0.5, 0.04, 'Frame', ha='center', fontsize=8)
    ax.figure.text(0.04, 0.5, 'Fluorescence', va='center', rotation='vertical', fontsize=8)


def generate_mip(nwb_obj):
    color_stack = nwb_obj.acquisition['NeuroPALImageRaw'].data[:]
    rgbw_indices = nwb_obj.acquisition['NeuroPALImageRaw'].RGBW_channels[:] - 1
    channel_gammas = nwb_obj.processing['NeuroPAL']['NeuroPAL_ID'].gammas[:]
    if color_stack.ndim < 4:
        print("Data format not as expected.")
        return np.zeros((100, 100, 3))
    max_img = color_stack.max(axis=1)
    rgb_img = np.zeros((max_img.shape[2], max_img.shape[1], 3), dtype=float)
    for i, chan_idx in enumerate(rgbw_indices[:3]):
        gamma = channel_gammas[chan_idx]
        channel_data = max_img[chan_idx, ...].astype(float)
        max_val = channel_data.max() if channel_data.max() != 0 else 1
        channel_data /= max_val
        channel_data = np.power(channel_data, 1.0 / gamma)
        channel_data *= max_val
        rgb_img[..., i] = channel_data.T
    return rgb_img


def visualize(nwb_obj):
    fig = plt.figure(figsize=(15, 15))
    gs = fig.add_gridspec(2, 2)
    ax_worm = fig.add_subplot(gs[0, 0])
    ax_neurons = fig.add_subplot(gs[0, 1])
    ax_video = fig.add_subplot(gs[1, 0])
    ax_activity = fig.add_subplot(gs[1, 1])

    plot_worm(ax_worm, nwb_obj)
    plot_neurons(ax_neurons, nwb_obj)
    plot_activity(ax_activity, nwb_obj)

    video_array = nwb_obj.acquisition['CalciumImageSeries'].data[1:75, :, :, :, :]
    if video_array.ndim < 5:
        print("Data format not as expected.")
        plt.show()
        return
    max_projection = video_array.max(axis=3)
    num_frames = min(75, max_projection.shape[0])
    rgb_frame = np.zeros((max_projection.shape[2], max_projection.shape[1], 3), dtype=video_array.dtype)
    for i, chan_idx in enumerate([0, 1, 2]):
        rgb_frame[..., i] = max_projection[0, :, :, chan_idx].T
    im = ax_video.imshow(rgb_frame, origin='lower')
    ax_video.axis('off')

    def update(frame_idx):
        for i, chan_idx in enumerate([0, 1, 2]):
            rgb_frame[..., i] = max_projection[frame_idx, :, :, chan_idx].T
        im.set_data(rgb_frame)
        ax_video.set_title(f"Frame {frame_idx}", loc='left', fontsize=8)
        return [im]

    ani = animation.FuncAnimation(fig, update, frames=num_frames, interval=100, blit=True)
    filename = f"{nwb_obj.subject.subject_id}_{datetime.now().strftime('%Y%m%d')}.mp4"
    ff_writer = animation.FFMpegWriter(fps=10)
    ani.save(filename=filename, writer=ff_writer)
