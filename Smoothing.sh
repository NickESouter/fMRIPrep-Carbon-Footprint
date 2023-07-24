#!/bin/bash

#Defines the identity of the pipeline being run. Will need to be updated accordingly.
pipeline="0"

#Defines a variable based on the location of files that have generated in fMRIPrep for processing in FEAT.
feat_folders="<directory root>/FEAT/Pipeline_${pipeline}/" #Full path removed for purpose of public sharing.

#Tells the script to just go one level deep such that we can iterate over subject subdirectories below.
subdirs=$(find "$feat_folders" -maxdepth 1 -type d | sort)

#Get the total number of subjects to be iterated over
total_subjects=$(find "$feat_folders" -maxdepth 1 -type d | grep -c "sub")

#Initialize a counter for the number of participants that have been iterated over
count=0

#Begins iterating over subjects.
for subdir in $subdirs

do
	#Defines the subject identity as a variable.
	subject=$(basename "$subdir")
	SUBJECTID="$subject"

	#The following is only done if the subdirectory found contains the string 'sub'.
	if [[ "$SUBJECTID" == *"sub"* ]]; then

		#Increment the counter for the number of participants that have been iterated over.
		((count++))

		#Changes the working directory to a 'Functional' subdirectory within the subject directory.		
		cd "${subdir}/Functional"		

		#Checks whether this 'Functional' directory exists. If not, the user is warned and the rest of the iteration is skipped.
		if [ $? -ne 0 ]; then
			echo "Functional subfolder not found for $SUBJECTID, smoothing has not been performed."
			continue
		fi

		#If they exist, output files for the below commands are deleted so that new versions can be created. Avoids issues where files
		#cannot be overwritten.
		find . -maxdepth 1 -name '*stopsignal_brain*' -type f -delete
		find . -maxdepth 1 -name '*3dFWHMx*' -type f -delete
		find . -maxdepth 1 -name '*smoothness*' -type f -delete

		#Smoothing starts here, using AFNI. Smoothing is run with a 5mm kernel, confined the to the 'mask' which effectively
		#performs brain extraction on the bold data during smoothing.
		3dBlurInMask -FWHM 5 -prefix stopsignal_brain -mask stopsignal_mask.nii.gz -input stopsignal_bold.nii.gz
		
		#The resulting AFNI files are converted to NIFTI format.
		3dAFNItoNIFTI stopsignal_brain+tlrc

		#The new uncompressed NIFTI file is compressed.
		fslchfiletype NIFTI_GZ stopsignal_brain.nii stopsignal_brain.nii.gz
		
		#First, estimates the smoothness of the bold data that has not been smoothed. This is masked by the 'mask' file.
		#The files used to generate the estimate are deleted to avoid overwriting issues, and then the same estimation
		#is performed on the smoothed data.
		3dFWHMx -geom -detrend -mask stopsignal_mask.nii.gz -out smoothness_pre -input stopsignal_bold.nii.gz
		find . -maxdepth 1 -name '*3dFWHMx*' -type f -delete
		3dFWHMx -geom -detrend -mask stopsignal_mask.nii.gz -out smoothness_post -input stopsignal_brain.nii.gz

		#Defines the smoothness output directory as a variable.
		smoothness_dir="${subdir}/Results/Smoothness"

		#If the smoothness directory already exists, any 'smoothness' files within are deleted to avoid overwriting
		#issues. If not, the directory is created.
		if [ -d "$smoothness_dir" ]; then
    			find "$smoothness_dir" -type f -name "*smoothness*" -delete
		else
    			mkdir -p "$smoothness_dir"
		fi

		#Moves the 4D smoothness estimates to the smoothness output directory.
		mv smoothness_pre $smoothness_dir
		mv smoothness_post $smoothness_dir

		#Checks whether each file in the working directory is either .json or .nii.gz. If not, it's deleted.
		#We won't need any other files going forward.
		ls | grep -vE '\.(nii\.gz|json)$' | xargs rm -f

		#Informs the user that the process is finished for a given subject.
		echo "Smoothing and estimations are complete for $SUBJECTID, $count/$total_subjects"

	fi

done
