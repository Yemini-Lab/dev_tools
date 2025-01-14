import os

def maedeh_decode_subject(subject_id):
    if "\\" in subject_id:
        subject_id = os.path.basename(subject_id)

    subject_list = subject_id.split('_')
    subject_list = subject_list[0].replace('sub-', '').split('-')

    reference_date = subject_list[0]
    reference_run = subject_list[1][1]

    return reference_date, reference_run