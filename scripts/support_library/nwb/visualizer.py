import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as mpatches
from matplotlib.patches import ConnectionPatch
from datetime import datetime


def plot_subject_info(ax, nwb_obj):
    ax.axis('off')
    subject_info = []
    if getattr(nwb_obj, 'subject', None) is not None:
        for attr in ['subject_id', 'age', 'description', 'genotype', 'sex', 'species', 'strain']:
            val = getattr(nwb_obj.subject, attr, None)
            if val is not None:
                subject_info.append(f"{attr.capitalize()}: {val}")
    if subject_info:
        info_text = "\n".join(subject_info)
    else:
        info_text = "No subject info available"
    ax.text(0, 0.5, info_text, ha='left', va='center', fontsize=10)


def plot_worm(ax, nwb_obj):
    rgb_img = generate_mip(nwb_obj)
    ax.imshow(rgb_img, origin='lower')
    ax.set_title(f"{nwb_obj.subject.subject_id} Colorstack", fontsize=10)
    ax.axis('off')


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
    if len(target_positions) > 0:
        sorted_indices = np.argsort(target_positions[:, 1])
        target_positions = target_positions[sorted_indices]
        target_labels = target_labels[sorted_indices]
    ax.imshow(rgb_img, origin='lower')
    ax.scatter(x_coords, y_coords, facecolors='none', edgecolors='w', s=20, alpha=0.6)
    if len(target_positions) > 0:
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
    ax.set_title(f"{nwb_obj.subject.subject_id} Neurons ({len(neuron_labels)})", fontsize=10)
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
        num_frames = max(len(a) for a in activity_values)
    else:
        ymin, ymax = 0, 1
        num_frames = 1  # fallback if no data

    # Get stimulus info
    stimulus_labels = nwb_obj.processing['CalciumActivity']['StimulusInfo'].data[:]
    stimulus_timestamps = nwb_obj.processing['CalciumActivity']['StimulusInfo'].timestamps[:]

    # Identify unique stimuli and assign colors
    unique_stimuli = np.unique(stimulus_labels)
    cmap = plt.cm.get_cmap('tab10', len(unique_stimuli))
    stimulus_colors = {label: cmap(i) for i, label in enumerate(unique_stimuli)}

    # Create a main 4x3 gridspec:
    # First row for legend (height ratio small), next three rows for the 3x3 plots
    main_spec = ax.get_subplotspec()
    main_gs = main_spec.subgridspec(4, 3, height_ratios=[0.3, 1, 1, 1])

    # Create legend_gs by sub-slicing the first row to a single subplot
    legend_gs = main_gs[0, :].subgridspec(1, 1)
    legend_ax = ax.figure.add_subplot(legend_gs[0, 0])

    # The neuron plots will occupy a 3x3 area: rows 1:4, all columns
    plot_gs = main_gs[1:4, :]

    # Now plot_gs is a 3x3 GridSpecFromSubplotSpec
    # Indexing plot_gs[row, col] returns a SubplotSpec
    axs = []
    for i in range(9):
        row, col = divmod(i, 3)
        axs.append(ax.figure.add_subplot(plot_gs[row, col]))

    # Shade and plot each neuron
    for idx, neuron in enumerate(target_neurons):
        subax = axs[idx]
        # Shade background according to stimuli
        for i in range(len(stimulus_labels)):
            start = stimulus_timestamps[i]
            if i < len(stimulus_labels) - 1:
                end = stimulus_timestamps[i + 1]
            else:
                end = num_frames  # last stimulus goes until end
            subax.axvspan(start, end, facecolor=stimulus_colors[stimulus_labels[i]], alpha=0.1)

        if neuron in activity_dict:
            fluo = activity_dict[neuron]
            subax.plot(fluo, linewidth=0.5, c='r')
            valid_fluo = [x for x in fluo if not np.isnan(x)]
            if valid_fluo:
                subax.set_ylim(ymin, np.max(valid_fluo) + 5)
            else:
                subax.set_ylim(ymin, ymax)
        else:
            # No activity found for this neuron
            subax.set_facecolor("lightgrey")
            subax.text(0.5, 0.5, "No activity found",
                       horizontalalignment='center', verticalalignment='center',
                       transform=subax.transAxes, color='black', fontsize=6)
            subax.set_ylim(ymin, ymax)

        subax.set_title(neuron, fontsize=8)
        # Only label y-axis on left column
        if idx % 3 != 0:
            subax.yaxis.set_ticklabels([])
            subax.set_ylabel('')
        else:
            subax.set_ylabel('Fluorescence', fontsize=6)

        # Only label x-axis on bottom row
        if idx < 6:
            subax.xaxis.set_ticklabels([])
            subax.set_xlabel('')
        else:
            subax.set_xlabel('Frame', fontsize=6)

        subax.tick_params(axis='both', which='major', labelsize=6)

    # Turn off any unused axes if target_neurons < 9
    for j in range(len(target_neurons), 9):
        axs[j].axis('off')

    # Create a legend for the stimuli in the legend_ax
    legend_handles = [mpatches.Patch(color=stimulus_colors[label], label=str(label)) for label in unique_stimuli]
    legend_ax.axis('off')
    legend_ax.legend(handles=legend_handles, loc='center', ncol=len(unique_stimuli), fontsize=8)

    plt.tight_layout()


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
    fig = plt.figure(figsize=(10, 10))
    gs = fig.add_gridspec(3, 2, height_ratios=[0.5, 3, 3], width_ratios=[3, 3])

    ax_info = fig.add_subplot(gs[0, :])
    plot_subject_info(ax_info, nwb_obj)

    ax_worm = fig.add_subplot(gs[1, 0])
    plot_worm(ax_worm, nwb_obj)

    ax_neurons = fig.add_subplot(gs[1, 1])
    plot_neurons(ax_neurons, nwb_obj)

    ax_video = fig.add_subplot(gs[2, 0])
    ax_activity = fig.add_subplot(gs[2, 1])
    plot_activity(ax_activity, nwb_obj)

    video_array = nwb_obj.acquisition['CalciumImageSeries'].data[1:75, :, :, :, :]
    if video_array.ndim < 5:
        print("Data format not as expected.")
        plt.tight_layout()
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
        ax_video.set_title(f"Calcium Imaging Series (t={frame_idx+1})", fontsize=10)
        return [im]

    ani = animation.FuncAnimation(fig, update, frames=num_frames, interval=100, blit=True)
    filename = f"{nwb_obj.subject.subject_id}_{datetime.now().strftime('%Y%m%d')}.mp4"
    ff_writer = animation.FFMpegWriter(fps=10)
    plt.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.05, wspace=0.3, hspace=0.3)
    ani.save(filename=filename, writer=ff_writer)
    plt.show()

