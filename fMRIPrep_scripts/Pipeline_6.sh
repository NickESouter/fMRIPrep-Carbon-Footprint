#!/bin/bash
#$ -N P6 #Job ID name sent to HPC cluster.
#$ -pe openmp 1 #Number of requested parallel environments.
#$ -o '/<directory root>/fMRIPrep/Pipeline_6/logs' #Folder where fMRIPrep logs files are saved out by the HPC cluster.
#$ -e logs #Resquests logs.
#$ -l m_mem_free=8G #Requested memory for HPC cluster.
#$ -l 'h=!nodeXXX&!nodeYYY&! #A list of problematic nodes to avoid when submitting tasks.
#$ -t 1-257 #This sets SGE_TASK_ID!, the number of subjects sent for preprocessing in this job (each is a seperate task).
#$ -tc 50 #The maximum number of tasks that can run simultaneously.

#Defines paths for (a) the input data, in BIDS format, (b) the folder in which working directory/scratch files should
#be generated, (c) the designated output folder for preprocesed data, (d) the location of fMRIPrep license file,
#and (e) the local FreeSurfer directory. With the excepton of input directory and license, each is edited to be pipeline-specific.
DATA_DIR=/<directory root>/CNP_BIDS
SCRATCH_DIR=/<directory root>/Pipeline_6/scratch
OUT_DIR=/<directory root>/Pipeline_6/derivatives
LICENSE=/<directory root>/fs_license/license.txt
LOCAL_FREESURFER_DIR=/<directory root>/Pipeline_6/derivatives/sourcedata/freesurfer

#Change current working directory to the input folder.
cd ${DATA_DIR}

#Return paths to subject directories that are located in BIDS directory. This should yield a shell array of subject IDs.
SUBJLIST=$(find sub-* -maxdepth 0  -type d)

#Define and print the number of subjects targetted.
len=${#SUBJLIST[@]}
echo Number of subjects  = $len

#Changes the working directory back to home
cd ${HOME}

#Prints out the index of the current task ID
echo This is task $SGE_TASK_ID

#Defines and prints the subject ID number, so this will be present within the log file. 
arr=($SUBJLIST)
SUBJECT=${arr[i]}
echo $SUBJECT

#Removes IsRunning files from the local FreeSurfer directory, if present. These files can cause problems if there
#are issues with overwriting.
find ${LOCAL_FREESURFER_DIR}/$SUBJECT/ -name "IsRunning" -type f -delete

#The fMRIPrep command line (see https://fmriprep.org/en/stable/usage.html for info on flags),
#with one flag adjusted according to pipeline ID.
singularity run --cleanenv \
    -B ${DATA_DIR}:/data \
    -B ${OUT_DIR}/:/out \
    -B ${SCRATCH_DIR}:/wd \
    -B ${LICENSE}:/license \
    /<directory root>/fmriprep_singularity/fmriprep_22.1.1.simg \
    --participant-label ${SUBJECT} \
    --fs-license-file /license \
    --skip-bids-validation \
    --work-dir /wd \
    --omp-nthreads 1 --nthreads 1 --mem_mb 30000 \ #P6: Threads reduced from 5 to 1.
    --output-spaces MNI152NLin6Asym:res-2 \
    --track-carbon \
    --country-code GBR \
    --ignore slicetiming \
    --random-seed 1234 \
    --skull-strip-fixed-seed \
    /data /out/ participant

echo Done
