#Imports relevant modules
import os
import csv

#Defines the path of the directory containing compiled data for all pipelines.
compiled_dir = '\\<directory root>\\Sustainability_Output\\Compiled'

#Defines the path of the directory that output data should be written into.
JASP_dir = '\\<directory root>\\JASP\\Output'

#Creates an empty dictionary to store all data, and a list to store subject IDs.
pipeline_data = {}
subjects = []

#Iterates over each pipeline.
for pipeline_file in os.listdir(compiled_dir):
 
    #Defines the ID of this pipeline, and adds a corresponding key to our dictionary,
    #with another dictionary as a value.
    pipeline = pipeline_file[:2]    
    pipeline_data[pipeline] = {}
    
    #Opens the compiled CSV file, and defines the headers as a list.
    with open(os.path.join(compiled_dir, pipeline_file), 'r') as compiled:
        reader = csv.reader(compiled)
        headers = next(reader)
        
        #Iterates over each header (dependent variable). Adds the relevant one as
        #keys to our pipeline-specific dictionary.
        for header in headers:
            if header in pipeline_data[pipeline] or header == 'Subject':
                continue
            else:
                pipeline_data[pipeline][header] = {}
        
        #Defines a list of DVs for this pipeline (should be the same for each).
        DV_list = list(pipeline_data[pipeline].keys())

        #Iterates over each row (subject) for our compiled CSV for this pipeline.
        for row in reader:          

            #Defines the subject ID as a variable.
            subject = row[0]
            
            #Skips those corresponding to the mean or SEM of data.
            if subject == 'Mean' or subject == 'SEM':
                continue
            
            #Unless they're already in there, adds the subject ID to our list.
            if subject not in subjects:
                subjects.append(subject)
            
            #Iterates over each item in the subject's row, tracks index.
            for i, thing in enumerate(row):
                
                #If an item has been flagged as an outlier, it's replaced with an empty cell.
                #Otherwise, the data point is added as a value to a dictionary corresponding
                #to the relevant pipeline, DV, and subject ID.
                if thing == 'N/A':
                    pipeline_data[pipeline][DV_list[i-1]][subject] = ''
                else:
                    pipeline_data[pipeline][DV_list[i-1]][subject] = thing

#Iterates over each of our dependent variables, and creates an output file for each.
for DV in DV_list:
    output_file = os.path.join(JASP_dir, '{}.csv'.format(DV))
    
    #This output file is opened, headers are written in according to available pipline IDs.
    with open(output_file, 'w', newline = '') as output:        
        writer = csv.DictWriter(output, lineterminator='\n', fieldnames = ['Subject'] + list(pipeline_data.keys()))
        writer.writeheader()
        
        #Iterates over each of our subjects, and creates a dictionary for each.
        for subject in sorted(subjects):        
            data_row = {'Subject': subject}
        
            #Adds in the data point for the relevant DV for each pipeline.
            for pipeline in pipeline_data.keys():
                data_row[pipeline] = pipeline_data[pipeline][DV][subject]
            
            #This dictionary is written into our output file as a row.
            writer.writerow(data_row)
