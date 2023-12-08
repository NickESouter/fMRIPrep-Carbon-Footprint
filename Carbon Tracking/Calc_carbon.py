
#!/usr/bin/env python
# Python Version: 3.10
# Author: Reese Wilkinson, Nick Souter
# Institution: University of Sussex
# Last Update: 01/11/2023
# Version 0.2.2


## Example 1:
# -bash$ qacct -j 3744147 |  python3 calc_carbon.py
# Job ID: 3744147
#        1:
#                 kWh: 0.000000
#                 gCO2: 0.000022
#                 kWh Requested: 0.000097
#                 gCO2 Requested: 0.018731
#        2:
#                 kWh: 0.000000
#                 gCO2: 0.000022
#                 kWh Requested: 0.000095
#                 gCO2 Requested: 0.018362

# Where qacct is the AGE queue accounting command, and 3744147 is the JOBID of the submitted array job for running the analysis.


## Example 2:
# -bash$ qacct -f carbon_jobs |  python3 calc_carbon.py
#        1:
#                 kWh: 0.000000
#                 gCO2: 0.000022
#                 kWh Requested: 0.000097
#                 gCO2 Requested: 0.018731
#        2:
#                 kWh: 0.000000
#                 gCO2: 0.000022
#                 kWh Requested: 0.000095
#                 gCO2 Requested: 0.018362

# Where we have one additional arg for qacct to specify the accounting file `carbon_jobs`, an example provided with this code.
# And we list all jobs in this file to process.


#######################################################################
##################### Imports #########################################
#######################################################################
#Imports relevant modules. All modules are python builtins.
import sys,os
import json
import argparse
import math

#######################################################################
##################### Global Variables ################################
#######################################################################

#Average volitile memory power consumption, per GBs, value taken from GA4HPC.
W_memory_per_GB = 0.3725

#Grams of carbon dioxide emitted per kWh hour of energy used. This is the 2022 average
#value for the UK, taken from https://www.carbonfootprint.com/international_electricity_factors.html
g_per_kWh = 193.38


#ARGPARSE GLOBALS/Defaults
SAVE_TO_JSON=True
PRINT_RESULT=True
MEM_CALC="ceiled"
PUE=1.28
JSON_DIR='Job_JSONs'
NODE_FILE="node_info.json"
CPU_FILE="cpu_info.json"
CPU_CALC="cputime"


#######################################################################
##################### Function Declarations ###########################
#######################################################################

# Check stdin filestream is not interactive and load it. The code expects logs to be piped into this script.                                               
def load_input_stream():
    if not sys.stdin.isatty():
        input_stream = sys.stdin
    return input_stream

#Opens and loads JSON files (specific to the University of Sussex HPC architecture)
#that contain information about nodes and CPUs in use.
def load_hpc_info():
    with open(NODE_FILE, 'r') as fin:
        node_info = json.load(fin)
        
    with open(CPU_FILE, 'r') as fin:
        cpu_info = json.load(fin)
        
    return node_info,cpu_info

#A function to convert energy used to estimated carbon emissions in grams.
def calc_carbon_in_g(energy, g_per_kWh=g_per_kWh):
    return energy * g_per_kWh

#A function to calculate CPU energy usage using runtime (hours) multiplied
#by thermal design power kW per core used, converted to kWH.
def calc_cpu_kWh(cpu,cpu_time):
    return cpu_time / 3600 * cpu["TDP"] / cpu["CPU"] / 1000

#A function to calculate memory energy use in kWh, based on the memory in GBs consumption of
#volatile memory consumed in the array. 
def calc_mem_kWh(mem,W_memory_per_GB=W_memory_per_GB):
    return mem * W_memory_per_GB / 3600 / 1000

#A function to calculate the energy requested/blocked for a given job, across CPU and RAM.
def calc_job_req_kWh(cpu,slots,wallclock,RAM,W_memory_per_GB=W_memory_per_GB):
    # Time in hours * TDP kW per core
    cpu_kWh = wallclock * slots / 3600 * cpu["TDP"]/cpu["CPU"] / 1000 
    ram_kWh = RAM * W_memory_per_GB / 3600 / 1000
    return cpu_kWh + ram_kWh

# Function to parse the input stream given it is the output from SGE/UGE qacct
def parse_sge_qacct(input_stream):
    #Creates an empty dictionary to store information about HPC jobs.
    #At default, the task ID, job ID, and hostname (node) are effectively empty.
    jobs = {}
    task_id = "notset"
    job_id = 0
    hostname = None

    #Goes through the 'qacct' output line by line and grabs job
    #information to store in dictionary for output and carbon calculations.
    for line in input_stream:

        #Checks whether the current job number can be found.
        if "jobnumber" in line:
            tmp = line.split()[1]
            if tmp!=job_id:
                job_id=tmp
                jobs[job_id]={}
            else:
                continue

        #Finds the node used to complete a given job.
        elif "hostname" in line and "=" not in line:
            hostname=line.split()[1]

        #Finds the specific ID for the current task.
        elif "taskid" in line and "pe" not in line:
            try:
                task_id = int(line.split()[1])
            except ValueError:
                if line.split()[1].strip()=="undefined":
                    task_id=0
            jobs[job_id][task_id]={"host":hostname}

        #Finds the duration of the task.
        elif "wallclock" in line and "ru_" not in line:
            if task_id=="notset":
                jobs[job_id][task_id]={"host":hostname}
            jobs[job_id][task_id]["wallclock"] = float(line.split()[1])

        # Finds the cputime of the jobs (ignores idl thread time)
        elif "cpu" in line:
            cpu_time = float(line.split()[1])
            jobs[job_id][task_id]["cpu"] = cpu_time

        #The same steps as above are repeated for RAM. We look for the consumed GBs of RAM for the job and
        #not the max memory consumed. Mem is the sum of ram_in_use*time_interval for the runtime of the jop.
        elif "mem " in line and "max" not in line:
            jobs[job_id][task_id]["mem"] = float(line.split()[1])            

        #The same steps as above are repeated for RAM. We look for peak memory consumed.
        elif "maxvmem" in line:
            maxvmem = line.split()[1]
            if "T" in maxvmem:
                maxvmem = float(maxvmem[:-1])*1000
            elif "G" in maxvmem:
                maxvmem = float(maxvmem[:-1])
            elif "M" in maxvmem:
                maxvmem = float(maxvmem[:-1])/1000
            elif "K" in maxvmem:
                maxvmem = float(maxvmem[:-1])/1e6
            else:
                maxvmem = float(maxvmem)/1e9
            jobs[job_id][task_id]["max_vmem"] = maxvmem

        #Finds the number of slots (cpu cores) used for a given task.
        elif "slots" in line:
            jobs[job_id][task_id]["NUM_CPU"] = int(line.split()[1])

        #Find and store the requested (blocked) memory for the job. Convert to GB if in MB.
        elif "hard_resources" in line:
            reqs = line.split()[1].split(",")
            RAM=None
            for res in reqs:
                if "h_vmem" in res:
                    request = res.split("=")[1]
                    if "G" in request:
                        RAM = float(request[:-1])
                    elif "M" in request:
                        RAM = float(request[:-1])/1000
            jobs[job_id][task_id]["RAM"] = RAM 
    return jobs


# Function to
def calulate_results(jobs, cpu_info, node_info):
    for job_id in jobs.keys():
        for task_id in jobs[job_id].keys():
            
            #Finds the memory used and how long for depending on switch case..
            #Calculates the energy use and estimated carbon footprint of the RAM time using the above functions.
            match MEM_CALC:
                case "integrated":
                    GB_mem_time = jobs[job_id][task_id]["mem"]
                case "ceiled":
                    GB_mem_time = math.ceil(jobs[job_id][task_id]["max_vmem"]) * jobs[job_id][task_id]["wallclock"]
                case "requested":
                    GB_mem_time = jobs[job_id][task_id]["RAM"] * jobs[job_id][task_id]["wallclock"]
            
            jobs[job_id][task_id]["mem_kWh"] = calc_mem_kWh(GB_mem_time)
            jobs[job_id][task_id]["mem_gCO2"] = calc_carbon_in_g(jobs[job_id][task_id]["mem_kWh"])
            
            #Finds the time a given CPU was in use depending on switch case, and extracts information from the CPU JSON file.
            #Calculates the energy use and estimated carbon footprint of the CPU using the above functions.        
            match CPU_CALC:
                case "cputime":
                    cpu_time = jobs[job_id][task_id]["cpu"]
                case "requested":
                    cpu_time = jobs[job_id][task_id]["NUM_CPU"] * jobs[job_id][task_id]["wallclock"]

            cpu = cpu_info[node_info[jobs[job_id][task_id]["host"]]]
            jobs[job_id][task_id]["cpu_kWh"] = calc_cpu_kWh(cpu, cpu_time)
            jobs[job_id][task_id]["cpu_gCO2"] = calc_carbon_in_g(jobs[job_id][task_id]["cpu_kWh"])
            
            #Calculates the total energy use and estimated emissions using values calculated above. Prints these values.
            jobs[job_id][task_id]["kWh"] = jobs[job_id][task_id]["cpu_kWh"]+jobs[job_id][task_id]["mem_kWh"]
            jobs[job_id][task_id]["gCO2"] = jobs[job_id][task_id]["cpu_gCO2"]+jobs[job_id][task_id]["mem_gCO2"]
    return jobs    

            

#Iterate through the calculated results and print to std.out the results. We iterate over jobs and task IDs.
def export_results(jobs):
    for job_id in jobs.keys():
        
        if PRINT_RESULT:
            print("\n\nJob ID: "+ job_id)

        #Iterates over each task that corresponds to a given job, prints the task RESULTS.
        for taskid in jobs[job_id].keys():
            if PRINT_RESULT:
                print("\t"+str(taskid)+": ")
                print("\t\t kWh: {:4f}".format(jobs[job_id][taskid]["kWh"]))
                print("\t\t gCO2: {:4f}".format(jobs[job_id][taskid]["gCO2"]))
            
        
        #Creates an output JSON file for this jobid and writes the calculated information into it.
        if SAVE_TO_JSON:
            with open( "{outdir}/calc_carbon_{job_id}.json".format(outdir=JSON_DIR,job_id=job_id),"w" ) as fout:
                json.dump({job_id: jobs[job_id]},fout,indent=2)

# Function to set global variables from command line arguments
def set_args(args):
    global W_memory_per_GB
    global g_per_kWh
    global SAVE_TO_JSON
    global PRINT_RESULT
    global MEM_CALC
    global JSON_DIR
    global NODE_FILE
    global CPU_FILE
    global CPU_CALC
    
    W_memory_per_GB=args.w_mem_per_GB
    g_per_kWh=args.CI
    SAVE_TO_JSON=args.save_to_json
    PRINT_RESULT=args.print_result
    MEM_CALC=args.memory_calc
    JSON_DIR=args.json_dir
    NODE_FILE=args.node_info
    CPU_FILE=args.cpu_info
    CPU_CALC=args.cpu_calc

#verify if the various paths/directories exist, and if not raise exception
def check_paths():
    if not os.path.exists(JSON_DIR):
        raise IOError("JSON Dir does not exist")
    elif not os.path.exists(CPU_FILE):
        raise IOError("CPU Info Json file does not exist",filename=CPU_FILE)
    elif not os.path.exists(NODE_FILE):
        raise IOError("Node Info Json file does not exist",filename=NODE_FILE)

#####################################################################################
####################### Main ########################################################
#####################################################################################

def main(args):
    
    # First we set globals from cmdline arguments
    set_args(args)
    
    # Check paths are correct
    check_paths()
    
    #Load inputs
    node_info,cpu_info = load_hpc_info()
    input_stream = load_input_stream()
    
    jobs = parse_sge_qacct(input_stream)
    
    jobs = calulate_results(jobs, cpu_info, node_info)
    
    export_results(jobs)
    
    
    
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--save-to-json',
                        action='store',
                        help="Write results to json output directory for each JOBID.",
                        default=SAVE_TO_JSON,
                        choices=[True,False],
                        type=bool)
    parser.add_argument("--json-dir", 
                        action='store',
                        help="Specificy directory to write json outputs to.",
                        default=JSON_DIR,
                        type=str)                
    parser.add_argument("--CI",
                        action='store',
                        help="Specify carbon intensity in g/kWh.",
                        default=g_per_kWh,
                        type=float)
    parser.add_argument("--print-result",
                        action='store',
                        help="Specify whether to print results to the command line.",
                        choices=[True,False],
                       default=PRINT_RESULT,
                       type=bool)
    parser.add_argument("--w_mem_per_GB",
                        action='store',
                        help="Specify the Eenrgy consumption of RAM, unit: Watts per GB.",
                        default=W_memory_per_GB,
                        type=float)
    parser.add_argument("--memory-calc",
                        action='store',
                        help="""Specify which method to use when calculating RAM usage.
                                ceiled: Max Vmem usage rounded up to nearest GB.
                                integrated: active RAM usage * cpu interval during job.
                                requested: RAM usage is set to requested RAM for job.
                            """,
                        default=MEM_CALC,
                        choices=["ceiled","integrated","requested"],
                        type=str)
    parser.add_argument("--cpu-calc",
                        action='store',
                        help="""Specify which method to use when calculating CPU usage.
                                cputime: Active cpu usage time. Does not include usage when threads idle.
                                requested: CPU slots requested multiplied by wallclock time of Job.
                            """,
                        default=CPU_CALC,
                        choices=["cputime","requested"],
                        type=str)
    parser.add_argument("--node-info",
                        action='store',
                        help="Specify the full filepath to the json containing node info.",
                        default=NODE_FILE,
                        type=str)
    parser.add_argument("--cpu-info",
                        action='store',
                        help="Specify path to cpu info json.",
                        default=CPU_FILE,
                        type=str)
    parser.add_argument
    args=parser.parse_args()
    
    main(args)
    

