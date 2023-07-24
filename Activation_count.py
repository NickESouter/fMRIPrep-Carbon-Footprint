#Imports relevant modules.
import os
import nibabel as nb
import numpy as np

#Defines the pipeline that we want to generate the activation count map for. This will need to be updated each time.
pipeline = '0'

#Based on the above variable, finds the directory corresponding to this pipeline which contains FEAT output.
pipeline_dir = '/<directory root>/FEAT/Pipeline_{}/'.format(pipeline) #Full path removed for purpose of public sharing.

#Defines the output directory for this pipeline. If this directory doesn't exist, it's created/
output_dir = '/<directory root>/Activation_Count/Pipeline_{}/'.format(pipeline) #Full path removed for purpose of public sharing.
if not os.path.isdir(output_dir):
	os.makedirs(output_dir)

#Creates a dictionary with contrasts of interest as keys and the corresponding zstat number as values.
contrasts = {'go': '1', 'stop': '2'}

#Iterates over each of our contrast.
for contrast in contrasts:

	#Creates a 'None' item that will soon be populated with an output array.
	count = None
	
	#Creates a variable to keep track of the number of subjects for this pipeline.
	subject_num = 0

	#Iterates over each subject for this pipeline.
	for subject in sorted(os.listdir(pipeline_dir)):

		#Ignores a given folder if it doesn't correspond to a specific subject. If it does, logs an additional subject in the total number.
		if 'sub' not in subject:
			continue
		else:
			subject_num += 1

		#The relevant thresholded zstat file for this contrast is located, loaded, and opened.
		contrast_file = os.path.join(pipeline_dir, subject, 'Results', '.feat', 'thresh_zstat{}.nii.gz'.format(contrasts[contrast]))
		contrast_load = nb.load(contrast_file)
		contrast_thr = contrast_load.get_fdata()
	
		#For the first subject being iterated over, the None type is replaced with an array with the shape of the input zstat file encountered here.
		if subject_num == 1:
			count = np.zeros(contrast_thr.shape)

		#Iterates through each voxel in our output array. If the respective voxel of the input file is above 0, '1' is added to this voxel location.
		for idx in np.ndindex(contrast_thr.shape):
			if contrast_thr[idx] > 0:
				count[idx] += 1

		print("Finished {} for {}, {} subjects processed.".format(subject, contrast, subject_num))

	#After the activation count array is complete, we generate a version that reflects the percent of the sample showing activation in each voxel.
	percent = count / subject_num * 100

	#A version of this array is created which is thresholded at voxels active in 5%+ of participants.
	percent_thr = percent.copy()
	percent_thr[percent_thr < 5] = 0

	#Defines a path for the output file path, turns it into a NIFTI image, and then saves it.
	percent_file = os.path.join(output_dir, 'Activation_count_P{}_{}.nii.gz'.format(pipeline, contrast))
	percent_img = nb.Nifti1Image(percent, contrast_load.affine, contrast_load.header)
	nb.save(percent_img, percent_file)

	#This process is repeated for the thresholded version of the output array.
	percent_thr_file = os.path.join(output_dir, 'Activation_count_P{}_{}_thr5.nii.gz'.format(pipeline, contrast))
	percent_thr_img = nb.Nifti1Image(percent_thr, contrast_load.affine, contrast_load.header)
	nb.save(percent_thr_img, percent_thr_file)
