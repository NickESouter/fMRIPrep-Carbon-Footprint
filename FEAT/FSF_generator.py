#Imports relevant modules
import glob
import os
import configparser
import shutil
import math

#Defines the pipeline that we're geneting FSF files for.
pipeline = '0'

#Defines filepaths of interest including (a) input directory containing preprocessed data,
#(b) the location where FSF files should be saved, and (c) the location of both FSF templates.
studydir = '/<directory root>/FEAT/Pipeline_{}/'.format(pipeline) #Full path removed for purpose of public sharing.
fsfdir = '/<directory root>/FEAT/Pipeline_{}/fsf_files/'.format(pipeline) #Full path removed for purpose of public sharing.
templates = '/<directory root>/FEAT/fsf_templates/' #Full path removed for purpose of public sharing.

#Checks whether the FSF directory exists. It's created if not.
if not os.path.exists(fsfdir):
	os.makedirs(fsfdir)

#If any items exist in the FSF folder, they're deleted.
for item in os.listdir(fsfdir):
	shutil.rmtree(os.path.join(fsfdir, item))

#These variables are used to calculate the number of batches, based on the target number of subjects
#per batch and the number of subjects in the input directory. Number is defined as the latter divided by
#the former, rounded up to the nearest whole number. We need these batches as we won't want to run
#FEAT for all subjects simultaneously.
batch_size = 13
num_subjects = len(os.listdir(studydir)) - 1
num_batches = math.ceil(num_subjects/batch_size)

#Defines the number of batches as an inclusive list with values between 1 and and the number of batches to be used.
batches = list(range(1, num_batches+1))

#If a batch number is below 10, a leading 0 is added to it to allow for alphabetisation.
for i, batch in enumerate(batches):
	if int(batch) < 10:
		batches[i] = f"0{batches[i]}"
	else:
		batches[i] = str(batches[i])

#Checks whether a folder exists for each batch. If not, it's created.
for batch in batches:

	batch_dir = os.path.join(fsfdir, 'Batch_{}'.format(batch))

	if not os.path.exists(batch_dir):
		os.makedirs(batch_dir)

#Iterates over subjects in the input directory.
for subject in sorted(os.listdir(studydir)):

	#Checks if there are already the max number of subjects in the current batch. If so, the first index of the batch list is removed.
	if len(os.listdir(os.path.join(fsfdir, 'Batch_{}'.format(batches[0])))) == batch_size:
		batches.pop(0)

	#Defines the batch directory as the first index of the list, which will change as a folder hits the max number of files (as above).
	batch_dir = os.path.join(fsfdir, 'Batch_{}'.format(batches[0]))

	#If a subfolder doesn't correspond to a specific subject, it's skipped.
	if 'sub' not in subject:
		continue

	#This dictionary contains template placeholders as keys, and replacement variables as values.
	replacements = {'SUBNUM': subject, 'PIPELINEID': 'Pipeline_{}'.format(pipeline)}

	#A subject-specific directory containing EV files.
	EV_dir = os.path.join(studydir, subject, 'EVs')

	#If this participant has an 'erroneous' EV, we'll use the 6 EV template and tell the user. If not,
	#we'll use the 5 ev template instead. Note that each EV subfolder will include X exprimental EVs plus
	#the confounds file. Finally, if the number of files in this folder is not 6 or 7, the user is told that
	#something weird is happening and the rest of the loop is skipped.
	if 'erroneous_trials.txt' in os.listdir(EV_dir) and len(os.listdir(EV_dir)) == 7:
		template = os.path.join(templates, 'EV6_template.fsf')
	elif 'erroneous_trials.txt' not in os.listdir(EV_dir) and len(os.listdir(EV_dir)) == 6:
		template = os.path.join(templates, 'EV5_template.fsf')
	else:
		print('Unexpected number of EVs for {}, investigate.'.format(subject))
		continue

	#A subject-specific output name for the FSF file.
	fsf_output = os.path.join(batch_dir, '{}_stopsignal_{}.fsf'.format(subject, pipeline))

	#Opens both the relevant template and the output file.
	with open(template) as infile:
		with open(fsf_output, 'w') as outfile:
			
			#Iterates over each line in the template.
			for line in infile:

				#Using the above dictionary, finds instances of placeholders and replaces them
				#with our target variables (pipeline ID and subject ID). The line is written into the 
				#output file with these replacements made.
				for placeholder, target in replacements.items():
					line = line.replace(placeholder, target)
				outfile.write(line)

#Defines the filepath that group fsf file will be saved to. This folder is created if it does not exist.
group_folder = '/<directory root>/Group_Level/Pipeline_{}/'.format(pipeline) #Full path removed for purpose of public sharing.
if not os.path.exists(group_folder):
	os.makedirs(group_folder)

#Defines the input and output group fsf files as variables.
group_template = os.path.join(templates, 'Group_template.fsf')
group_output = os.path.join(group_folder, 'Group_stopsignal_{}.fsf'.format(pipeline))

#Opens the input and output files.
with open(group_template) as group_in:
	with open(group_output, 'w') as group_out:
		
		#Iterates over each line in the template.
		for line in group_in:

			#Finds any instance of the pipeline ID placeholder, and replaces.
			line = line.replace('PIPELINEID', 'Pipeline_{}'.format(pipeline))
			group_out.write(line)
