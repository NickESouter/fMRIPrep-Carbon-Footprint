#Imports relevant modules
import os
import numpy as np
import csv

#Defines the directory containing pipeline results.
feat_dir = '/<directory root>/FEAT/' #Full path removed for purpose of public sharing.

#Defines the pipeline we're interested in.
pipeline = '0'

#Defines the filepath of this pipeline.
pipeline_dir = os.path.join(feat_dir, 'Pipeline_{}'.format(pipeline))

#Creates a path for an output file for this pipeline and defines its headers in a list.
output_path = '/<directory root>/Smoothness/Pipeline_{}_smoothness.csv'.format(pipeline) #Full path removed for purpose of public sharing.
headers = ['Subject', 'Pre', 'Post', 'Pre_x', 'Pre_y', 'Pre_z', 'Post_x', 'Post_y', 'Post_z']

#The output file is opened and headers are written in.
with open(output_path, mode = 'w', newline = '') as output_file:
	writer = csv.DictWriter(output_file, fieldnames = headers)
	writer.writeheader()

	#Iterates over each subject in the directory for this pipeline.
	for subject in os.listdir(pipeline_dir):

		#Ignores a given folder if it doesn't correspond to a specific subject.
		if 'sub' not in subject:
			continue

		#This dictionary will store smoothness values for a given dimension for a given timepoint (pre-/post-smoothing).
		dimensions = {'pre_x': [], 'pre_y': [], 'pre_z': [], 'post_x': [], 'post_y': [], 'post_z': []}

		#Iterates over the possible variants of the smoothing estimate files (pre- and post-smoothing).
		for suffix in ['pre', 'post']:

			#Defines the smoothing file that we're interested in.
			smoothing_file = os.path.join(pipeline_dir, subject, 'Results', 'Smoothness', 'smoothness_{}'.format(suffix))

			#Opens and reads this file, then iterates over each row inside, which is stripped and split into numerical values.
			with open(smoothing_file, 'r') as file:
				for line in file:
					row = line.strip().split()

					#'float' versions of all values are appended to the respective list based on timepoint and dimension.
					dimensions['{}_x'.format(suffix)].append(float(row[0]))
					dimensions['{}_y'.format(suffix)].append(float(row[1]))
					dimensions['{}_z'.format(suffix)].append(float(row[2]))

		#Iterates over each key in the dictionary.
		for dimension in dimensions.keys():

			#Defines a high and low cutoff for detecting outliers (+/-3 standard deviations from the mean of this dimension).
			high_cutoff = np.mean(dimensions[dimension]) + 3*np.std(dimensions[dimension])
			low_cutoff =  np.mean(dimensions[dimension]) - 3*np.std(dimensions[dimension])

			#Any values found to exceed these cutoffs are removed from the repsective list.
			for i in dimensions[dimension]:
				if i >= high_cutoff or i <= low_cutoff:
					dimensions[dimension].remove(i)					
			
		#Data for this subject are written into their output file, using the relevant mean values.
		subject_row = {'Subject': subject,
			 	'Pre': np.mean(dimensions['pre_x'] + dimensions['pre_y'] + dimensions['pre_z']),
			 	'Post': np.mean(dimensions['post_x'] + dimensions['post_y'] + dimensions['post_z']),
			 	'Pre_x': np.mean(dimensions['pre_x']),
			 	'Pre_y': np.mean(dimensions['pre_y']),
			 	'Pre_z': np.mean(dimensions['pre_z']),
			 	'Post_x': np.mean(dimensions['post_x']),
			 	'Post_y': np.mean(dimensions['post_y']),
			 	'Post_z': np.mean(dimensions['post_z'])}
		writer.writerow(subject_row) 
