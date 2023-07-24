#!/bin/bash

#The pipeline ID we're using. This will need to be actively updated.
pipeline="0"

#The FEAT directory for this pipeline is defined.
feat_dir="/<directory root>/FEAT/Pipeline_${pipeline}/" #Full path removed for purpose of public sharing.

#Changes the working directory to the one containing FSF files for this pipeline.
cd /<directory root>/FEAT/Pipeline_${pipeline}/fsf_files #Full path removed for purpose of public sharing.

#Iterates over each batch subfolder within this pipeline fsf directory.
for batch_dir in */; do

	#Change working directory to the current batch.
	cd "$batch_dir"

	#Loops over all .fsf files for this batch.
	for subject in *.fsf; do

		#FEAT is then run on this file in the background, such that other files in this batch will run simultaneously.
		feat $subject &
	done

	#Prints a message that FEAT has started for this batch.
	echo "Starting FEAT for ${batch_dir%/}." 

	#Waits for all background processes to complete before finishing this batch.
	wait

	#Prints a message indicating that this batch has finished processing.
	echo "Finished FEAT for ${batch_dir%/}." 

	#Changes working directory back to the parent directory.
	cd ..

done

#From here, we need to iterate over the output folders for each subject and make changes to files generated during registration.
#Group-level analysis requires registration to have been run at this stage, but we've already registered. I followed the steps detailed
#here: https://www.youtube.com/watch?v=U3tG7JMEf7M&t=482s

#Looks for each subject within the FEAT directory.
find "$feat_dir" -type d -name "*sub*" -print0 | while IFS= read -r -d '' subject; do

	#Defines a path of this subject's results folder, checks whether it exists.
	feat_path="$subject/Results/.feat/"
	if [ -d "$feat_path" ]; then

		#Deletes any existing .mat files from the 'reg' folder.
		rm -f "$feat_path/reg/"*.mat

		#Copies the following files to the respective destinations (re-registered data is overwritten).
		cp "$FSLDIR/etc/flirtsch/ident.mat" "$feat_path/reg/example_func2standard.mat"
		cp "$feat_path/mean_func.nii.gz" "$feat_path/reg/standard.nii.gz"

		#Generates transformation and summary images that we'll need for Featquery to run successfully.
		updatefeatreg $feat_path -gifs

	fi
done

#Creates an array which contains each ROI as keys, with the number of the respective zstat file as values.
#These will be used to run Featquery below.
declare -A ROIs
ROIs=( ["Motor"]="1" ["Pre-sma"]="2" ["Auditory"]="2" ["Insula"]="2" )

#Iterates over each batch subfolder within this pipeline directory, again.
for batch_dir in */; do
	
	#Prints a message to signal that Featquery is running for this batch.
	echo "Running Featquery for $batch_dir"

	#Change working directory to the current batch.
	cd "$batch_dir"

	#Loops over all .fsf files for this batch.
	for subject in *.fsf; do

		#Defines subject ID as a varaible in the format we'll need it.
		subject=${subject%%_*}

		#Iterates over each ROI.
		for roi in "${!ROIs[@]}"; do
			
			#Defines the value of this ROI as the zstat code we'll need.
			zstat=${ROIs[$roi]}
			
			#Runs Featquery on the respective ROI for this batch. This will run simultaneously across all subjects in a batch for the respective ROI.
			featquery 1 ${feat_dir}${subject}/Results/.feat/ 1 stats/zstat$zstat featquery_$roi /research/cisc1/projects/rae_sustainability/CNP/Activation_coordinates/ROIs/${roi}_ROI.nii.gz &

		done
	wait

	done


	#Change working directory back to the parent directory.
	cd ..

done
