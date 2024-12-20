import math


def validate_subject(nwb_obj):
    expected_sexes = ['O', 'X']
    expected_species = 'http://purl.obolibrary.org/obo/NCBITaxon_6239'

    issue_list = []

    if nwb_obj.subject.sex not in expected_sexes:
        issue_list.append('subject sex')

    if nwb_obj.subject.species != expected_species:
        issue_list.append('subject species')

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
        if module_obj.imaging_volume.grid_spacing[:] != expected_grid_spacing:
            issue_list.append(f"{each_acquisition_module} grid_spacing")

        channels = module_obj.imaging_volume.optical_channel
        for each_channel in channels:
            if (
                    each_channel.name not in expected_channels
                    or each_channel.emission_range[:] == [0, 0]
                    or each_channel.emission_lambda == 0
                    or each_channel.excitation_range[:] == [0, 0]
                    or each_channel.excitation_lambda == 0
            ):
                issue_list.append(f"{each_acquisition_module} channel: {each_channel.name}")

    return issue_list


def validate_processed(nwb_obj):
    expected_keys = ['CalciumActivity', 'NeuroPAL']
    expected_calcium_data = ['ActivityTraces', 'StimulusInfo', 'TrackedNeurons']
    expected_neuropal_data = ['NeuroPALSegmentation', 'NeuroPAL_ID', 'TrackedNeurons']

    issue_list = []

    processing_modules = list(nwb_obj.processing.keys())
    for each_processing_module in processing_modules:
        if each_processing_module.name not in expected_keys:
            issue_list.append('processing keys')

        each_data_interface = list(each_processing_module.data_interfaces.keys())
        if (
                each_data_interface != expected_calcium_data
                or each_data_interface != expected_neuropal_data
        ):
            issue_list.append(f"{each_processing_module} data interface: {each_data_interface.name}")

        for each_child in each_data_interface:
            match each_child.__class__.__name__:
                case 'DynamicTable':
                    for each_column in each_child.colnames:
                        if each_column.name == "Activity":
                            if math.isnan(each_column[:]):
                                issue_list.append(f"{each_processing_module} {each_child.name} contains nan values")

                case 'AnnotationSeries':
                    if each_child.data.shape != each_child.timestamps.shape:
                        issue_list.append(f"{each_processing_module} {each_child.name} data/timestamp dim mismatch")

                case 'ImageSegmentation':
                    if each_child.name == 'TrackedNeurons':
                        tracked_rois = each_child['TrackedNeuronROIs'].voxel_mask
                        if len(tracked_rois.shape) < 2:
                            issue_list.append(
                                f"{each_processing_module} {each_child.name} video rois compressed along time dimension")

                        non_zero = [0, 0, 0]
                        for roi in tracked_rois[:]:
                            if roi[0] != 0:
                                non_zero[0] = 1

                            if roi[1] != 0:
                                non_zero[1] = 1

                            if roi[2] != 0:
                                non_zero[2] = 1

                        if non_zero[0] != 1:
                            issue_list.append(
                                f"{each_processing_module} {each_child.name} video rois all zero along first dim (x?)")

                        if non_zero[1] != 1:
                            issue_list.append(
                                f"{each_processing_module} {each_child.name} video rois all zero along second dim (y?)")

                        if non_zero[2] != 1:
                            issue_list.append(
                                f"{each_processing_module} {each_child.name} video rois all zero along third dim (z?)")

                case _:
                    issue_list.append(f"{each_processing_module} unexpected child class: {each_child.name}")

    return issue_list
