import math

def visualize_worm(nwb_obj):
    subject = nwb_obj.subject
    color_stack = nwb_obj.acquisition['NeuroPALImageRaw'].data[:]
    rgbw = nwb_obj.acquisition['NeuroPALImageRaw'].RGBW_channels[:]


def visualize_video(nwb_obj):
    subject = nwb_obj.subject
    video_array = nwb_obj.acquisition['CalciumImageSeries'].data[:]
    rgbw = nwb_obj.acquisition['CalciumImageSeries'].RGBW_channels[:]


def visualize_activity(nwb_obj):
    target_neurons = ['AWA', 'I2', 'AVA', 'AVB', 'VB2']
    activity_module = nwb_obj.processing['CalciumActivity']['ActivityTraces']

    activity_dict = {}
    for n in range(len(activity_module.neuron)):
        neuron_name = activity_module.neuron[n]
        if neuron_name in target_neurons:
            activity_dict[neuron_name] = activity_module.activity[n]
