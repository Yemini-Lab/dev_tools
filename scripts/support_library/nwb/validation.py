import math

import numpy as np
import pynwb.misc
import pynwb.ophys
import hdmf.common.table


def validate_subject(nwb_obj):
    expected_sexes = ['O', 'X']
    expected_species = 'http://purl.obolibrary.org/obo/NCBITaxon_6239'

    issue_list = []

    if nwb_obj.subject.sex not in expected_sexes:
        issue_list.append('Sex: invalid')

    if nwb_obj.subject.species != expected_species:
        issue_list.append('Species: invalid')

    if nwb_obj.subject.strain == "[]":
        issue_list.append('Strain: not specified')

    if not issue_list:
        return ["Subject: PASSED"]
    else:
        return issue_list


def validate_acquisitions(nwb_obj):
    expected_keys = ['CalciumImageSeries', 'NeuroPALImageRaw']
    expected_grid_spacing = [0.4, 0.4, 1.5]
    expected_channels = ['BFP', 'CyOFP', 'GCaMP', 'RFP', 'mNeptune']

    issue_list = []

    acquisition_modules = list(nwb_obj.acquisition.keys())
    if acquisition_modules != expected_keys:
        issue_list.append('acquisition keys')

    for each_acquisition_module in acquisition_modules:
        module_obj = nwb_obj.acquisition[each_acquisition_module]
        if any(module_obj.imaging_volume.grid_spacing[:] != expected_grid_spacing):
            issue_list.append(f"{each_acquisition_module} grid_spacing")

        channels = module_obj.imaging_volume.optical_channel
        for each_channel in channels:
            if (
                    each_channel.name not in expected_channels
                    or any(each_channel.emission_range[:] == [0, 0])
                    or each_channel.emission_lambda == 0
                    or any(each_channel.excitation_range[:] == [0, 0])
                    or each_channel.excitation_lambda == 0
            ):
                issue_list.append(f"{each_acquisition_module}: channel {each_channel.name} contains filler info")

    if not issue_list:
        return ["Acquisitions: PASSED"]
    else:
        return issue_list


def validate_processed(nwb_obj):
    expected_keys = ['CalciumActivity', 'NeuroPAL']
    expected_calcium_data = ['StimulusInfo', 'TrackedNeurons', 'ActivityTraces']
    expected_neuropal_data = ['NeuroPALSegmentation', 'TrackedNeurons', 'NeuroPAL_ID']

    issue_list = []

    for module_name, processing_module in nwb_obj.processing.items():
        if module_name not in expected_keys:
            issue_list.append(f"Unexpected processing key: {module_name}")

        data_interfaces = list(processing_module.data_interfaces.keys())
        if data_interfaces not in [expected_calcium_data, expected_neuropal_data]:
            issue_list.append(f"{module_name} has unexpected data interfaces: {data_interfaces}")

        for interface_name, each_child in processing_module.data_interfaces.items():
            if isinstance(each_child, hdmf.common.table.DynamicTable):
                if "Activity" in each_child.colnames:
                    activity_column = each_child["Activity"]  # Access the column properly
                    if any(math.isnan(val) for val in activity_column.data):
                        issue_list.append(f"{module_name} {interface_name} contains NaN values in Activity column")

            elif isinstance(each_child, pynwb.misc.AnnotationSeries):
                if each_child.data.shape != each_child.timestamps.shape:
                    issue_list.append(f"{module_name} {interface_name} data/timestamp dim mismatch")

            elif isinstance(each_child, pynwb.ophys.ImageSegmentation):
                if each_child.name == 'TrackedNeurons':
                    tracked_rois = np.array(each_child['TrackedNeuronROIs'].voxel_mask[:].tolist())
                    if tracked_rois.shape[1] < 3:
                        issue_list.append(f"{module_name} {interface_name} ROI compressed along time dimension")

                    non_zero = (tracked_rois > 0).any(axis=(0, 1))
                    if not non_zero:
                        issue_list.append(f"{module_name} {interface_name} ROI has all-zero slices along dimensions")

            else:
                issue_list.append(f"{module_name} unexpected child class: {type(each_child).__name__}")

    if not issue_list:
        return [".processing Modules: PASSED"]
    else:
        return issue_list


def validate(nwb_obj):
    issue_list = []

    subject_issues = validate_subject(nwb_obj)
    if len(subject_issues) > 0:
        issue_list += subject_issues

    acquisition_issues = validate_acquisitions(nwb_obj)
    if len(acquisition_issues) > 0:
        issue_list += acquisition_issues

    processing_issues = validate_processed(nwb_obj)
    if len(processing_issues) > 0:
        issue_list += processing_issues

    is_valid = len(issue_list) == 0
    summary = '\n '.join(issue_list)

    return is_valid, summary