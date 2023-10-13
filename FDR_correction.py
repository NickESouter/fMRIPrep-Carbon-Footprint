#Imports relevant modules.
import os
import csv

#Defines the path of the FDR directory.
FDR_dir = '\\<directory root>\\JASP\\FDR'

#Defines paths for the input and output folders we'll need.
Input_dir = os.path.join(FDR_dir, 'Input')
Corrected_dir = os.path.join(FDR_dir, 'Corrected')

#Iterates over the input files (one per DV).
for input_file in os.listdir(Input_dir):
    
    #This file is opened, and the first line is read out.
    input_f = open(os.path.join(Input_dir, input_file), 'r')    
    input_f.readline()

    #Creates a list to store data for each of our comparisons.
    comparisons = []
    
    #Iterates over each row in the input file, which is stripped and split by comma.
    for line in input_f.readlines():        
        line = line.strip().split(',')
       
        #We add a dictionary to our above list containing the identity of this comparison,
        #t-value, and p-value (converted to float so we can sort them)
        comparisons.append({'Comparison': line[0], 't_val': float(line[1]), 'p_val': float(line[2])})        
    
    #Our comparisons list is sorted in ascending by the p-value of each dictionary.
    comparisons.sort(key = lambda x: x['p_val'])
    
    #The output file is defined and opened, and the header row is written.
    output_f = open(os.path.join(Corrected_dir, '{}_corrected.csv'.format(input_file[:-4])), 'w')    
    writer = csv.DictWriter(output_f, lineterminator='\n', fieldnames = ['Comparison', 't', 'p', 'p_corr'])
    writer.writeheader()    
    
    #Again, iterates over each of our comparisons, tracking index.
    for i, comparison in enumerate(comparisons):
        
        #Saves out info into the output file. This includes all information in the input
        #dictionary as well as corrected p-value. This is calculated using the Benjamini-Hochberg method.
        #Specificially, the p-value is multiplied by the number of comparisons. This value
        #is divided by the rank of the p-value relative to others.
        comp_row = {'Comparison': comparisons[i]['Comparison'],
                    't': comparisons[i]['t_val'],
                    'p': comparisons[i]['p_val'],
                    'p_corr': (comparison['p_val'] * len(comparisons))/(i+1)}
        writer.writerow(comp_row)        
    
    #Both the input and output files are closed.
    input_f.close()
    output_f.close()