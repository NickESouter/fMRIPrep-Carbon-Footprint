#Imports relevant modules
import os
import nibabel as nb
import numpy as np

#Defines the pipeline ID.
pipeline = '0'

#Defines the path in which FEAT output is stored for this pipeline.
pipeline_dir = '/<directory root>/FEAT/Pipeline_{}'.format(pipeline) #Full path removed for purpose of public sharing.

#Creates an empty list to store subjects' data.
stats_list = []

#Iterates over each subject, skipping any folders that don't correspond to a subject.
for subject in sorted(os.listdir(pipeline_dir)):

	if 'sub' not in subject:
		continue

	#Defines the path in which statistical results can be found for this subject.
	stats_path = os.path.join(pipeline_dir, subject, 'Results', '.feat', 'stats')	
		
	#Finds one of the stats file, and opens it (we only use zstat1 as zstat 2 is a perfect inverse).
	stats_file = os.path.join(stats_path, 'zstat1.nii.gz')
	stats_load = nb.load(stats_file)
	stats_matrix = stats_load.get_fdata()

	#Adds a matrix containing all z-stats for this subject to the above list.
	stats_list.append(stats_matrix)
	
	#Prints that processing is finished for this subject.
	print("Finished {}".format(subject))

#Prints that group level map is now generating.
print("Generating group map...")

#Stacks the subjects' matrices, providing a 4D matrix.
stacked_stats = np.stack(stats_list, axis = -1)

#Caclulates the standard deviation of z-stats at each voxel across this 4th dimension (subject)
stats_sd = np.std(stacked_stats, axis = -1)

#Defines the name of the output file to be created.
output_file = '/<directory root>//Sustainability_Output/Activation_SD_Map/P{}_Activation_SD_Map.nii.gz'.format(pipeline)

#Updates header information for this file.
header = stats_load.header.copy()
header.set_data_shape(stats_sd.shape)

#Names the resulting file, and saves it out.
SD_file = nb.Nifti1Image(stats_sd, stats_load.affine, header)
nb.save(SD_file, output_file)
