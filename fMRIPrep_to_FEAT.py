#Imports relevant modules.
import os
import shutil
import csv
import nibabel as nb
import numpy as np

#Defines the version of the pipeline being run
pipeline = '0'

#Defines the directory containing the fMRIPrep derivatives folder for this pipeline.
derivatives = '/<directory root>/fMRIPrep/Pipeline_{}/derivatives/'.format(pipeline) #Full path removed for purpose of public sharing.

#A function to copy relevant files.
def copy_file(input_folder, input_file, output_folder, copy_name):
	
	#Firt, identifies the suffix (filetype) of the input file by finding the first instance of '.'
	first_decimal = input_file.find('.')
	suffix = input_file[first_decimal:]	

	#The path to be copied is defined. If it's a TXT file, the suffix is ignored
	#as this will be automatically applied anyway. If not, suffix is included in the link name.
	if 'txt' in suffix:
		copy_path = os.path.join(subdirectories[output_folder], copy_name)
	else:
		copy_path = os.path.join(subdirectories[output_folder], (copy_name + suffix))	

	#Checks if a given file exists. If so, it's removed so it can be rewritten.
	if os.path.exists(copy_path):
		os.remove(copy_path)

	#Copy of the file is created.
	shutil.copy(os.path.join(input_folder, input_file), copy_path)	

#A counter for the number of subjects processed.
sub_count = 0

#Iterates through each subject in the derivatives directory.
for subject_ID in sorted(os.listdir(derivatives)):

	#Checks whether the given element within this directory actually corresponds to a subject. If not, it's skipped.
	if 'sub' not in subject_ID or 'html' in subject_ID:
		continue

	#Prints out the subject ID and number of subjects who have been processed.
	sub_count += 1
	print("Now processing {}, subject #{}".format(subject_ID, sub_count))
	
	#Defines the FEAT output directory where this participant's files will be stored.
	output_directory = '/<directory root>/FEAT/Pipeline_{}/{}'.format(pipeline, subject_ID) #Full path removed for purpose of public sharing.

	#Creates a dictionary which defines type of data as keys, and appropriate filepath names as values.
	subdirectories = {'structural': os.path.join(output_directory, 'Structural'), 'functional': os.path.join(output_directory, 'Functional'),
	'EVs': os.path.join(output_directory, 'EVs'), 'results': os.path.join(output_directory, 'Results'),
	'behav': os.path.join(output_directory, 'Behav'), 'confounds': os.path.join(output_directory, 'Confounds')}

	#Iterates through this dictionary. Checks if a given path exists. If not, it's created.
	for sub in subdirectories.keys():

		if not os.path.exists(subdirectories[sub]):
			os.makedirs(subdirectories[sub])

	#Defines the 'func' and 'anat' input directories as variables.
	func_folder = os.path.join(derivatives, subject_ID, 'func')
	anat_folder = os.path.join(derivatives, subject_ID, 'anat')

	#A dictionary that will be used to store our motion nuisance regressor values. Each variable of
	#interest includes an empty list as a value. Numbers will be appended below.
	confound_dict = {'trans_x': [], 'trans_y': [], 'trans_z': [], 'rot_x': [], 'rot_y': [], 'rot_z': []}

	#Iterates through each file in the functional directory.
	for func_file in os.listdir(func_folder):						
				
		#Checks for the files that were interested in, including (a) the preprocessed bold file, 
		#(b) a brain mask for this run, and (c) confounds relating to movement etc. Each file we're interested in will have
		#a corresponding JSON file. Both will be identified with this loop/function and copied to the appropriate folder.
		if 'preproc_bold' in func_file and 'res-2' in func_file:
			copy_file(func_folder, func_file, 'functional', 'stopsignal_bold')

		if 'brain_mask' in func_file and 'res-2' in func_file:
			copy_file(func_folder, func_file, 'functional', 'stopsignal_mask')

		if 'confounds' in func_file:
			copy_file(func_folder, func_file, 'confounds', 'stopsignal_confounds')

			#This extra step for the confound TSV opens the file and pulls out the information that we're
			#interested in, which is then added to the confounds ditctionary created above. Any 'n/a' values
			#are entered as 0, others are kept in their original form.
			if 'tsv' in func_file:
			
				confounds_file = os.path.join(func_folder, func_file)
	
				with open(confounds_file, 'r') as open_confounds:

					confounds_reader = csv.DictReader(open_confounds, delimiter = '\t')

					for row in confounds_reader:
						for confound_key in confound_dict.keys():

							if row[confound_key] == 'n/a':
								confound_dict[confound_key].append('0')
							else:
								confound_dict[confound_key].append(row[confound_key])

	#Creates a text file that will be used to store motion confounds for input to FEAT. This file is opened to be written into.
	confounds_file = os.path.join(subdirectories['EVs'], 'confounds.txt')
	with open(confounds_file, 'w') as f:

		#Iterates through the number of rows in the first confound (number of volumes)
		for i in range(len(confound_dict['trans_x'])):

			#Creates a list storing all relevant confound values for the respective volume, using the dictionary created above.
			volume_list = [confound_dict['trans_x'][i], confound_dict['trans_y'][i], confound_dict['trans_z'][i],
			confound_dict['rot_x'][i], confound_dict['rot_y'][i], confound_dict['rot_z'][i]]

			#Creates a string using these values, which is then written into the confounds file.
			volume_string = ' '.join(str(measure) for measure in volume_list)
			f.write(volume_string + '\n')
		
	#The same process as above is used to copy structural files.
	for anat_file in os.listdir(anat_folder):

		if 'preproc_T1w' in anat_file and 'res-2' in anat_file:
			copy_file(anat_folder, anat_file, 'structural', 'T1w')

		if 'brain_mask' in anat_file and 'res-2' in anat_file:
			copy_file(anat_folder, anat_file, 'structural', 'T1w_brain')

	#A variable is created to correspond to the location of this participant's EV files.
	EV_data = '/<directory root>/EVs/{}'.format(subject_ID) #Full path removed for purpose of public sharing.

	#Iterates over each EV, and copies it to the new location.
	for EV_file in os.listdir(EV_data):
		copy_file(EV_data, EV_file, 'EVs', EV_file)

	#Defines the path of this participant's behavioural data.
	behav_data = '/<directory root>/BIDS_dir/{}/beh'.format(subject_ID) #Full path removed for purpose of public sharing.

	#Iterates through files in this directory and copies them to the new location.
	for behav_file in os.listdir(behav_data):			
		copy_file(behav_data, behav_file, 'behav', 'stopsignal_behav')
