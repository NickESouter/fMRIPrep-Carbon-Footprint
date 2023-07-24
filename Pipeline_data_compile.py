#Imports relevant modules.
import os
import numpy as np
import csv

#Defines the pipline ID. This will need to be updated.
pipeline = '4'

#Defines the filepath containing all output files.
data_folder = '/<directory root>/Sustainability_Output' #Full path removed for purpose of public sharing.

#Defines the path of each specific file we'll need.
carbon_file = os.path.join(data_folder, 'Calc_Carbon', 'Pipeline_{}_carbon_HPC.csv'.format(pipeline))
smoothness_file = os.path.join(data_folder, 'Smoothness', 'Pipeline_{}_smoothness.csv'.format(pipeline))
featquery_file = os.path.join(data_folder, 'Featquery', 'Pipeline_{}_Featquery.csv'.format(pipeline))

#Creates a list containing all measures we're interested in.
measures = ['Duration', 'Emissions', 'CPU_kWh', 'Memory_kWh', 'Smoothness_Pre', 'Smoothness_Post',
'Motor', 'Pre-SMA', 'Auditory', 'Insula']

#A dictionary to store data for each subject.
subjects = {}

#Opens the files for carbon, smoothness, and featquery. Iterates over each row for each and then adds
#the relevant data to the respective subject's dictionary key.
with open(carbon_file, newline = '') as carbon:

	carbon_rows = csv.reader(carbon, delimiter = ',', quotechar = '"')	
	next(carbon_rows)

	for row in carbon_rows:

		#Duration is converted from seconds to hours.
		subjects[row[0]] = {'Duration': float(row[5])/3600,
			'Emissions': row[16],
			'CPU_kWh': row[7],
			'Memory_kWh': row[10]}
	
with open(smoothness_file, newline = '') as smoothness:

	smoothness_rows = csv.reader(smoothness, delimiter = ',', quotechar = '"')	
	next(smoothness_rows)

	for row in smoothness_rows:

		subjects[row[0]]['Smoothness_Pre'] = row[1]
		subjects[row[0]]['Smoothness_Post'] = row[2]

with open(featquery_file, newline = '') as featquery:

	featquery_rows = csv.reader(featquery, delimiter = ',', quotechar = '"')	
	next(featquery_rows)

	for row in featquery_rows:

		subjects[row[0]]['Motor'] = row[1]
		subjects[row[0]]['Pre-SMA'] = row[2]
		subjects[row[0]]['Auditory'] = row[3]
		subjects[row[0]]['Insula'] = row[4]

#Adds keys for the mean and standard error of the mean to the subject dictionary.
subjects['Mean'] = {}
subjects['SEM'] = {}

#Iterates over each of our measures.
for measure in measures:

	#An empty dictionary to store data points for each subject, and a list that will
	#store the same values seperately from subject ID.
	all_data_dict = {}
	all_data_list = []

	#Starts a count of the number of outliers identified.
	outlier_count = 0

	#Iterates over each subject, skips them if they refer to the mean of SEM of a measure.
	for subject in subjects:

		if subject == 'Mean' or subject == 'SEM':
			continue

		#The data point for this subject/measure is added to the list and dictionary.
		all_data_dict[subject] = float(subjects[subject][measure])
		all_data_list.append(float(subjects[subject][measure]))

	#Defines a high and low cutoff for identifying outliers.
	high = np.mean(all_data_list) + 3*np.std(all_data_list)
	low = np.mean(all_data_list) - 3*np.std(all_data_list)

	#Iterates over each subject again.
	for subject in all_data_dict:

		#Defines the value of this subject/measure
		val = all_data_dict[subject]

		#If a given value classes as an outlier, it's replaced by 'N/A'.
		if val > high or val < low:
			subjects[subject][measure] = 'N/A'
			outlier_count += 1

	#Prints how many outliers have been removed for a given measure.
	print("{} outlier(s) removed for {}.".format(outlier_count, measure))

	#Creates a new list to exclude any N/A values. Then iterates over each subject again
	#and adds relevant values to this new list.
	outliers_removed = []

	for subject in subjects:

		if subject == 'Mean' or subject == 'SEM':
			continue

		val = subjects[subject][measure]

		if val != 'N/A':
			outliers_removed.append(float(val))

	#Adds the mean and SEM for this measure to the subject's dictionary.
	subjects['Mean'][measure] = np.mean(outliers_removed)
	subjects['SEM'][measure] = np.std(outliers_removed)/np.sqrt(len(outliers_removed))

#Defines the filepath of the output file and puts all headers in a list.
output_path = os.path.join(data_folder, 'Compiled', 'P{}_Compiled_HPC.csv'.format(pipeline))
headers = ['Subject'] + measures

#Opens the output file and writes the headers.
with open(output_path, mode = 'w', newline = '') as output_file:
	writer = csv.DictWriter(output_file, fieldnames = headers)
	writer.writeheader()
	
	#Feeds the relevant information for each subject into the output file. Each row is written.
	for subject in subjects:
		print(subject)
		out_data = {'Subject': subject,
		'Duration': subjects[subject]['Duration'],
		'Emissions': subjects[subject]['Emissions'],
		'CPU_kWh': subjects[subject]['CPU_kWh'],
		'Memory_kWh': subjects[subject]['Memory_kWh'],
		'Smoothness_Pre': subjects[subject]['Smoothness_Pre'],
		'Smoothness_Post': subjects[subject]['Smoothness_Post'],
		'Motor': subjects[subject]['Motor'],
		'Pre-SMA': subjects[subject]['Pre-SMA'],
		'Auditory': subjects[subject]['Auditory'],
		'Insula': subjects[subject]['Insula']}
		writer.writerow(out_data)
