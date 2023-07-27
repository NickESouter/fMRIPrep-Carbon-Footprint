#Imports relevant modules
import os
import csv

#Sets the pipeline. This will need to be updated manually.
pipeline = '0'

#Defines the directory containing fMRIPrep pipeline output.
pipeline_dir = '/<directory root>/FEAT/Pipeline_{}'.format(pipeline) #Full path removed for purpose of public sharing.

#Creates a path for the output file for this pipeline and defines the relevant headers in a list.
output_path = '/<directory root>/Featquery/Pipeline_{}_Featquery.csv'.format(pipeline) #Full path removed for purpose of public sharing.
headers = ['Subject', 'Motor', 'Pre-sma', 'Auditory', 'Insula']

#The output file is opened and the header row is written.
with open(output_path, mode = 'w', newline = '') as output_file:
	writer = csv.DictWriter(output_file, fieldnames = headers)
	writer.writeheader()

	#Iterates over each subject in the pipeline directory.
	for subject in sorted(os.listdir(pipeline_dir)):

		#A folder is skipped if it doesn't contain the 'sub' string.
		if 'sub' not in subject:
			continue

		#Creates a dictionary for this subject which just contains their ID.
		zstats = {'Subject': subject}

		#Iterates over each ROI in the headers dictionary, skipping the 'subject' header.
		for region in headers:
			if region == 'Subject':
				continue
			
			#Defines a path to the relevant featquery report for this region.	
			featquery_report = os.path.join(pipeline_dir, subject, 'Results', '.feat', 'featquery_{}'.format(region), 'report.txt')

			#Opens the report, and pulls out the mean zstat value.
			with open(featquery_report, 'r') as f:
					mean_stat = f.readline().split()[5]

			#This value is added to the above dictionary with the region label as a key.
			zstats[region] = mean_stat

		#The subject-specific dictionary is written into the output file as a row.
		writer.writerow(zstats)
