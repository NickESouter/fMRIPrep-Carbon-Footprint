#Imports relevant modules.
import os
import nibabel as nb
import numpy as np

#Defines the pipeline that we want to generate the SD map for. This will need to be updated each time.
pipeline = '0'

#Based on the above variable, finds the directory corresponding to this pipeline which contains fMRIPrep output.
pipeline_dir = '/mnt/lustre/users/psych/ns605/Sustainability/fMRIPrep/Pipeline_{}/derivatives/'.format(pipeline)

#Creates an empty object that we'll use to create a single 'union' mask for this pipeline.
union_mask_data = None
affine = None

#Here, we'll make our mask for this pipeline. The result will be a mask that accounts for all voxels that
#are non-zero in any subject in the sample. First, iterates over each subject.
for subject in sorted(os.listdir(pipeline_dir)):

	#Skips any that don't correspond to a subject folder.
	if 'sub' not in subject or 'html' in subject:
		continue

	#Prints that this subject is being iterated over.
	print("Processing mask for {}".format(subject))

	#Defines a path containing the functional output data for this subject.
	func_path = os.path.join(pipeline_dir, subject, 'func')

	#Checks for the occurrence of the below strings in this folder. The resolution of
	#the volumetric output space used is accordingly defined as a variable.
	for filename in os.listdir(func_path):
		if 'res-2' in filename:
			resolution = '2'
			break
		elif 'res-1' in filename:
			resolution = '1'
			break

	#Reads in this subject's individual mask.
	mask_file = os.path.join(func_path, '{}_task-stopsignal_space-MNI152NLin6Asym_res-{}_desc-brain_mask.nii.gz'.format(subject, resolution))
	mask_img = nb.load(mask_file)
	mask_data = mask_img.get_fdata().astype(bool)
	
	#If union_mask_data is not initialized, initialize it with the shape of the first mask.
	if union_mask_data is None:
		union_mask_data = np.zeros(mask_data.shape, dtype=bool)
		affine = mask_img.affine

	#Take the union of the current mask with the union_mask_data.
	union_mask_data = np.logical_or(union_mask_data, mask_data)

#Saves the resulting union mask out as a variable.
brain = union_mask_data.astype(np.uint8)

#Now we can move on to create the SD map. First, creates a variable to store the running sum of SD maps.
running_sum = None

#This variable will be used to keep track of how many subjects have been iterated over.
count = 0

#Iterates over each subject in the fMRIPrep directory, again.
for subject in sorted(os.listdir(pipeline_dir)):

	#Ignores a given folder if it doesn't correspond to a specific subject.
	if 'sub' not in subject or 'html' in subject:
		continue

	#1 is added to the subject count.
	count += 1

	#Defines a path containing the functional output data for this subject.
	func_path = os.path.join(pipeline_dir, subject, 'func')

	#Checks for the occurrence of the below strings in this folder. The resolution of
	#the volumetric output space used is accordingly defined as a variable.
	for filename in os.listdir(func_path):
		if 'res-2' in filename:
			resolution = '2'
			break
		elif 'res-1' in filename:
			resolution = '1'
			break

	#Finds and opens the preprocessed timeseries file.
	timeseries_file = os.path.join(func_path, '{}_task-stopsignal_space-MNI152NLin6Asym_res-{}_desc-preproc_bold.nii.gz'.format(subject, resolution))
	timeseries_load = nb.load(timeseries_file)
	timeseries_raw = timeseries_load.get_fdata()

	#This subject-specific data is multiplied by our above brain file, such that the timeseries data is masked by the sample's union brain mask.
	#The 3D array is adjusted to account for the fact it's being multiplied by a 4D array.
	timeseries = timeseries_raw * brain[..., np.newaxis]

	#Calculate the SD of timeseries values within each voxel across the fourth dimension (time) for this subject.
	timeseries_sd = np.std(timeseries, axis=3)

	#Update the running sum with the current SD map
	if running_sum is None:
		running_sum = timeseries_sd
	else:
		running_sum += timeseries_sd

	#A message is printed, informing the user of the subject ID and the percent of participants now completed.
	print("Finished {}, {:.1f}% done.".format(subject, count / 257 * 100))

print("Calculating the mean map...")

#Calculate the mean map by dividing the running sum by the number of subjects
mean_map = running_sum / count

#The name of the output file for this pipeline is defined.
output_file = '/research/cisc2/projects/rae_sustainability/Sustainability_Output/SD_Map/P{}_SD_Map.nii.gz'.format(pipeline)

#Creates a new NIFTI header for the output file given that it's now 3D, not 4D.
header = timeseries_load.header.copy()
header.set_data_shape(mean_map.shape)

#The output file is created and saved.
mean_map_file = nb.Nifti1Image(mean_map, timeseries_load.affine, header)
nb.save(mean_map_file, output_file)
