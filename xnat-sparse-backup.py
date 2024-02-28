import os
import pyxnat

# XNAT connection parameters
xnat_url = 'https://mri.lavlab.mcw.edu'
username = 'admin'
password = '!Sh3rm4N?!Sh3rm4N?'

# Local directories for DICOM and ROI files
local_dir = 'local_directory'

# Connect to XNAT server
connection = pyxnat.Interface(server=xnat_url, user=username, password=password)

# Get all the projects
projects = connection.select.projects()

# Iterate through the projects
for project in projects:
    project_id = project.id()
    # Get all the subjects in the current project
    subjects = project.subjects()
    # Iterate through the subjects
    for subject in subjects:
        subject_id = subject.id()
        print(subject_id)
        # Get all the experiments (sessions) for the current subject
        experiments = subject.experiments()

        # Iterate through the experiments
        for experiment in experiments:
            experiment_id = experiment.id()
            print(experiment_id)
            # Get all the scans for the current experiment
            scans = experiment.scans()
            output_dir = os.path.join(local_dir, project_id, subject_id, experiment_id)
            roi_output_dir = os.path.join(local_roi_dir, project_id, subject_id, experiment_id)
            # pyxnat.resources.
            # scans.download(output_dir, type='DICOM', extract=True)
            # scans.download(roi_output_dir, type='ROI', extract=True)
            # Iterate through the scans
            for scan in scans:
                scan_id = scan.id()
                print(scan_id)
                    
                os.makedirs(output_dir, exist_ok=True)
                scan.resource('NIFTI').get(output_dir, True)

                # os.makedirs(roi_output_dir, exist_ok=True)
                # scan.resources('OHIF').get(roi_output_dir, True)

                # Download DICOM files
                # scan.download(output_dir, type='DICOM')

                # Download ROI files
                # scan.download(output_dir, type='DICOM')

# Disconnect from the XNAT server
connection.disconnect()