# Measuring and reducing the carbon footprint of fMRI preprocessing in fMRIPrep

This repository contains a collection of Python and Shell scripts used for the project 'Measuring and reducing the carbon footprint of fMRI preprocessing in fMRIPrep'. This study did not involve novel data collection, but made use of an existing repository. The scripts included here were used to process and analyse data. The application and use of each is summarised below. Summaries here are ordered according to the order in which they would have been run for a given pipeline. Within each script, comments are provided to comprehensively document the intention of each section.

For all scripts detailed below (with the exception of the pipeline-specific fMRIPrep scripts), the user must open the script and manually update the 'pipeline' variable towards the top, depending on which pipeline was being run. For instance, for Pipeline 0 this would simply be 
```
pipeline = '0'
```

## fMRIPrep Scripts

This folder contains shell scripts used to run each of our ten fMRIPrep pipeline variants. These scripts were all submitted to the University of Sussex high performance cluster (LINK) with the command:

```
qsub -jc test.long Pipeline_{X}.sh
```
 This indicates that this job should be registered as job class 'test.long'. Each script operates as an array, such that all subjects within the specified input BIDS directory were run as individual task in a single job. With the specified job class, each job was allocated 150 CPUs (typically translating to 30 jobs running at a given time, given that each task requests 5 CPUs).
 
 ## Carbon_extract.py
 
This Python script pulls CodeCarbon metrics from the output of a given pipeline, by cross-referencing the fMRIPrep 'emissions.csv' file with the fMRIPrep logs for each task in the pipeline input directory. A number of data points are pulled for each subject and are put into a pipeline-specific CSV file in the specified output directory:

 * Subject ID
 * fMRIPrep start time/date
 * fMRIPrep end time/date
 * Duration in seconds
 * Duration in hours
 * Estimated carbon emissions in CO2eq (kg)
 * Rate of emissions (emissions/time)
 * CPU power used
 * RAM power used
 * CPU energy used
 * RAM energy used
 * Total energy used, across CPU and RAM

## SD_MAP.py

At this stage, we can extract the 'standard deviation (SD) map' for the respective pipeline. This involves calculating the SD of timeseries values across all timepoints within a given subject (for each voxel). In doing so, the 4D input file is converted to a 3D array. The mean standard deviation for each voxel is then calculated across subjects. This provides a measure of variaiblity within the timeseries, where higher variability may suggest lower precision of spatial normalisation and therefore reduced anatomical specificity. An output NIFTI file is generated in the specified location for the respective pipeline.

This script can take a little while to run. It'll print out when the individual-level maps for each subject have finished processing, as well as the % of the sample that's now been covered.

## fMRIPrep_to_FEAT.py

This Python script identifies target fMRIPrep output files, and moves them into a format that makes it easier to process data in FSL FEAT, with an output directory specific to the pipeline in question. Directories created for a given subject and pipeline include:

* **Behavioural** data for a given subject's stop signal run. Not actually used in analysis, but may be useful to refer back to.
* Motion **Confounds** identified by fMRIPrep, these will be used in FEAT.
* **EVs** reflecting timing information for each period of interest for a given subject's stop signal run. Will be used to build the FEAT model for the respective subject.
* **Functional** files including the subject's preprocessed BOLD run and brain mask, will be used to generate the smoothed file that will go on to be used in FSL FEAT.
* An empty **Results** folder that will be used to store subsequent data.
* **Structural** scans for this subject, including preprocessed T1w scan and the relevant brain mask.

## Smoothing.sh

This shell script is used to smooth the preprocessed BOLD data for a given subjects, and provide mean estimates of smoothness for this data both pre- and post-smoothing, with BOLD data masked by the subject's brain mask. Both smoothing and estimations are performed in AFNI. Output files are converted into a nifti format that can be used in FEAT, and any files we won't go on to use are deleted. Wil print a message in the terminal reflecting the end of smoothing for a given subject, as well as a progress counter for how many subjects have been smoothed relative to the number in the input directory. 

This generates a smoothed output NIFTI file that will serve as the input for FSL FEAT, as well as txt files containing mean estimates of smoothing in the aformentioned **Results** directory for a given subject. Seperate files are generated for the pre- and post-smoothing estimates, with one value for each of the x, y, and z dimensions for each volume (x184).

## Smoothing_average.py

This Python script pulls out mean smoothness estimates for each subject within a given pipeline, and then combines all of them into a single CSV file within the specified output directory. For each subject, seperately for the pre- and post-smoothed data, this provides:

* The overall mean smoothness value across all volumes (x184) and dimensions (x3)
* The mean value within the x dimension across all volumes
* The mean value within the y dimension across all volumes
* The mean value within the z dimension across all volumes

At each level, outliers are removed by excluding any values 3 standard deviations above or below the mean of the respectvie dimension when calculating the average.

## fsf_generator.py

This Python script is used to create the fsf files needed to run FSL FEAT. Given that each subject only has one run of the stop signal task, just one fsf file per subject is needed. This pipeline's higher-level group fsf file is also generated in a seperate directory. This script uses fsf templates, which are included in this repositroy in the 'fsf_templates' folder. For first-level files, the template used depends on whether the subject has 5 or 6 EVs present (depending on whether the subject presented with any erroneous 'go' trials or not).

Given that FEAT jobs were run directly in the terminal rather than on our HPC cluster, output files for a given pipeline are divided into batches of 13 each (an arbitrary number). This allows one to run each pipeline's FEAT jobs in chunks to avoid overloading the system (e.g., with 257 submitted at once). The size/number of each batch can be modulated within the script by increasing or decreasing value assigned to the 'batch_size' variable.

For me, this automated generation must be followed by an irritating manual step of opening each fsf file in the FSL FEAT GUI, and resaving them under the same name. This will generate the necessary extra files (e.g., .mat and .con) that are needed to automate the running of FEAT jobs. At present, I have not discovered a way of automating the generation of these extra files. This must also be done for the group level fsf file.

## Run_FEAT.sh

This shell script runs first-level FEAT jobs and FEATQUERY roi analysis for a given pipeline. This includes several steps.

* Iterates through each batch (see above) of fsf files, and runs each one in FEAT. Prints a message when a given batch has started, and when it's finished.
* It's then encessary to iterate over the output folders for each subject and make changes to files generated during registration. FSL group-level analysis requires registration to have been run at the first level, but we've already registered during fMRIPrep. Registration is therefore left on in the fsf template, and we need to clean up afterwards. I followed the steps detailed here: https://www.youtube.com/watch?v=U3tG7JMEf7M&t=482s
* Using a number of pre-specified ROI masks relevant to the stop signal task, FEATQUERY ROI analysis is then run on the relevant zstat file. Descriptive statistics of z-statistics within each ROI for the respective contrast are extracted in a report that ends up in the subject's first-level FEAT output folder.

## Featquery_extract.py

This Python scripts runs through the FEAT output directory for each subject for a specific pipeline, and extracts the mean z-statistic in each ROI. This data is exported to a pipeline-specific CSV file in the output directory specified.

## Activation_count.py

This Python script creates an 'activation count map' for a given pipeline. This involves taking thresholded statistical maps from FSL FEAT as input. For each voxel, the percentage of the sample showing activation across the sample is calculated. This is done for both contrasts that we're interested in (favouring 'go' or 'successful stop'). NIFTI files are saved as output in the specified directory. A version of the maps that are threholded at 25% activation across the sample is also saved (this is the threshold used in visualisation by Esteban et al. (2019), although our data rarely reach this thresholded given that we used a more stringent statistical threshold of Z = 3.1).

## Group_level_extract.py

There will only be one group-level fsf file generated per pipeline, so I just manually run this in the terminal using

```
feat <path to group fsf>
```
Following this, this Python script simply pulls out thresholded statistical maps for both contrasts, and places them in the specificied output directory for this pipeline.

## Pipeline_data_compile.py

Above, we've pulled out a number of dependent variables for the measures of CodeCarbon, smoothness estimates, and task activation. This script combs across these output files for a given pipeline and creates a cleaner/simplifies overall output file, which includes only the variables that will be used in formal analysis. This includes, for each subject:

* Duration of fMRIPrep in hours
* Estimated carbon emissions of fMRIPrep in CO2eq kg
* CPU energy used for fMRIPrep
* RAM energy used for fMRIPrep
* Overall mean smoothness for pre-smoothed data
* Overall mean smoothness for post-smoothed data
* Mean z-statistic in the Motor ROI
* Mean z-statistic in the Pre-SMA ROI
* Mean z-statistic in the Auditory ROI
* Mean z-statistic in the Insula ROI

For each variable, individual subject data points are marked as outliers and excluded (replaced by 'N/A') if they are 3 standard deviations above or below the mean value of the respective value. A CSV file containing all these variables for a given pipeline is placed into the specified output directory.
