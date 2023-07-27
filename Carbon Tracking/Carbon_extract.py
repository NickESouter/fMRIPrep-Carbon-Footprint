#Imports relevant modules.
import os
import csv
import json

#Defines the pipeline of interest.
pipeline = '0'

#Defines the pipeline directory as a variable.
pipeline_dir = '/<directory root>/fMRIPrep/Pipeline_{}'.format(pipeline) #Full path removed for purpose of public sharing.

#Defines the location of the directory containing JSON files for each HPC job.
job_json_dir = '/<directory root>/Calc_Carbon/Job_JSONs' #Full path removed for purpose of public sharing.

#Defines the fieldnames to be used in the output file.
fieldnames = ['Subject', 'Log', 'Node', 'Num_CPU', 'RAM', 'Wallclock', 'CPU', 'CPU_kWh', 'CPU_gCO2', 'Memory', 'Memory_kWh', 'Memory_gCO2', 'kWh', 'gCO2', 'kWh_req', 'gCO2_req', 'kgCO2']

#Defines the fMRIPrep log directory for this pipeline.
log_dir = os.path.join(pipeline_dir, 'logs')

#Defines the name of the output file to be created.
output_file = '/<directory root>/Sustainability_Output/Calc_Carbon/Pipeline_{}_carbon_HPC.csv'.format(pipeline) #Full path removed for purpose of public sharing.

#This output file is opened to be written into, and headers are written.
with open(output_file, 'w', newline = '') as csv_file:
	writer = csv.DictWriter(csv_file, fieldnames = fieldnames)
	writer.writeheader()

	#Iterates over each log in the log directory.
	for log in os.listdir(log_dir):

		#Defines a job and task IDs by splitting the log file name and pulling out relevant aspects.
		job = str(log.split('.')[-2][1:])
		task = str(log.split('.')[-1])

		#Opens the fMRIPrep log file, and pulls out the subject ID as a variable.
		with open(os.path.join(log_dir, log), 'r') as log_file:
			for line in log_file:
				if 'sub-' in line:
					subject = line.strip()
					break

		#Points to the specific json for the job relating to this log file. Skips if this file doesn't exist.
		job_json = os.path.join(job_json_dir, 'calc_carbon_{}.json'.format(job))

		if not os.path.exists(job_json):
			continue

		#At default, logs that a dictionary has not been found for this specific task.
		dict_found = False

		#Opens the job-specific JSON file and loads the data.
		with open(job_json) as json_file:
			data = json.load(json_file)

			#Checks whether the task ID for this log file can be found in the relevant job file. If so, the dictionary for
			#this task is pulled out and the above variable is updated to 'True'. If not, a warning is printed.
			if task not in data[job].keys():
				print("Not found for {}.{}, {}".format(job, task, pipeline))
			else:
				task_dict = data[job][task]
				dict_found = True

		#If a dictionary was found for this log file, relevant data is written into the output file. If not, N/A values are written in.
		if dict_found == True:
					
			subject_row = {'Subject': subject,
			'Log': log,
			'Node': task_dict['host'],
			'Num_CPU': task_dict['NUM_CPU'],
			'RAM': task_dict['RAM'],
			'Wallclock': task_dict['wallclock'],
			'CPU': task_dict['cpu'],
			'CPU_kWh': task_dict['cpu_kWh'],
			'CPU_gCO2': task_dict['cpu_gCO2'],
			'Memory': task_dict['mem'],
			'Memory_kWh': task_dict['mem_kWh'],
			'Memory_gCO2': task_dict['mem_gCO2'],
			'kWh': task_dict['kWh'],
			'gCO2': task_dict['gCO2'],
			'kWh_req': task_dict['kWh_req'],
			'gCO2_req': task_dict['gCO2_req'],
			'kgCO2': float(task_dict['gCO2'])*0.001}
			writer.writerow(subject_row)

		else:

			subject_row = {'Subject': subject,
			'Log': log,
			'Node': 'N/A',
			'Num_CPU': 'N/A',
			'RAM': 'N/A',
			'Wallclock': 'N/A',
			'CPU': 'N/A',
			'CPU_kWh': 'N/A',
			'CPU_gCO2': 'N/A',
			'Memory': 'N/A',
			'Memory_kWh': 'N/A',
			'Memory_gCO2': 'N/A',
			'kWh': 'N/A',
			'gCO2': 'N/A',
			'kWh_req': 'N/A',
			'gCO2_req': 'N/A',
			'kgCO2': 'N/A'}
			writer.writerow(subject_row)
