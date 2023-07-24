#Imports relevant modules
import os
import shutil

#Defines the pipline ID as a variable. WIll need to be updated.
pipeline = '0'

#Defines input and output folders.
in_dir = '/<directory root>/Group_Level/Pipeline_{}/.gfeat/'.format(pipeline) #Full path removed for purpose of public sharing.
out_dir = '/<directory root>/Sustainability_Output/Group_Level/Pipeline_{}/'.format(pipeline) #Full path removed for purpose of public sharing.

#Checks if the output directory exists, creates it if not.
if not os.path.exists(out_dir):
	os.makedirs(out_dir)

#Creates a dictionary with contrast labels as keys and cope numbers as values.
contrasts = {'Go': '1', 'Stop': '2'}

#For each contrast, defines the specific input and output filepaths for each contrast, then copies the file over.
for contrast in contrasts:
	in_path =  os.path.join(in_dir, 'cope{}.feat'.format(contrasts[contrast]), 'thresh_zstat1.nii.gz')
	out_path = os.path.join(out_dir, '{}_Group_P{}.nii.gz'.format(contrast, pipeline))
	shutil.copyfile(in_path, out_path)
