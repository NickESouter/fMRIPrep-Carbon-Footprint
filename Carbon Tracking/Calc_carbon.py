
#!/usr/bin/env python
# Author: Reese Wilkinson, Nick Souter
# Institution: University of Sussex
# Last Update: 01/11/2023
# Version 0.2.2


## Example:
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

#Imports relevant modules. All modules are python builtins.
import sys
import json

#Global variables.

#Average volitile memory power consumption, per GBs, value taken from GA4HPC.
W_memory_per_GB = 0.3725

#Grams of carbon dioxide emitted per kWh hour of energy used. This is the 2022 average
#value for the UK, taken from https://www.carbonfootprint.com/international_electricity_factors.html
g_per_kWh = 193.38

# Check stdin filestream is not interactive and load it. The code expects logs to be piped into this script.                                               
if not sys.stdin.isatty():
    input_stream = sys.stdin

#Opens and loads JSON files (specific to the University of Sussex HPC architecture)
#that contain information about nodes and CPUs in use.
with open("node_info.json", 'r') as fin:
    node_info = json.load(fin)
    
with open("cpu_info.json", 'r') as fin:
    cpu_info = json.load(fin)

#Creates an empty dictionary to store information about HPC jobs.
#At default, the task ID, job ID, and hostname (node) are effectively empty.
jobs = {}
task_id = "notset"
job_id = 0
hostname = None

#A function to convert energy used to estimated carbon emissions in grams.
def calc_carbon_UK_in_g(energy, g_per_kWh=g_per_kWh):
    return energy * g_per_kWh

#A function to calculate CPU energy usage using runtime (hours) multiplied
#by thermal design power kW per core used, converted to kWH.
def calc_cpu_kWh(cpu,cpu_time):
    return cpu_time / 3600 * cpu["TDP"] / cpu["CPU"] / 1000

#A function to calculate memory energy use in kWh, based on the memory in GBs consumption of
#volatile memory consumed in the array job. 
def calc_mem_kWh(mem,W_memory_per_GB=W_memory_per_GB):
    return mem * W_memory_per_GB / 3600 / 1000

#A function to calculate the energy requested/blocked for a given job, across CPU and RAM.
def calc_job_req_kWh(cpu,slots,wallclock,RAM,W_memory_per_GB=W_memory_per_GB):
    # Time in hours * TDP kW per core
    cpu_kWh = wallclock * slots / 3600 * cpu["TDP"]/cpu["CPU"] / 1000 
    ram_kWh = RAM * W_memory_per_GB / 3600 / 1000
    return cpu_kWh + ram_kWh

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
        task_id = int(line.split()[1])
        jobs[job_id][task_id]={"host":hostname}

    #Finds the duration of the task.
    elif "wallclock" in line and "ru_" not in line:
        jobs[job_id][task_id]["wallclock"] = float(line.split()[1])

    #Finds the time a given CPU was in use, and extracts information from the CPU JSON file.
    #Calculates the energy use and estimated carbon footprint of the CPU using the above functions.
    elif "cpu" in line:
        cpu_time = float(line.split()[1])
        jobs[job_id][task_id]["cpu"] = cpu_time
        cpu = cpu_info[node_info[hostname]]
        jobs[job_id][task_id]["cpu_kWh"] = calc_cpu_kWh(cpu, cpu_time)
        jobs[job_id][task_id]["cpu_gCO2"] = calc_carbon_UK_in_g(jobs[job_id][task_id]["cpu_kWh"])

    #The same steps as above are repeated for RAM. We look for the consumed GBs of RAM for the job and
    #not the max memory consumed. Mem is the sum of ram_in_use*time_interval for the runtime of the jop.
    elif "mem " in line and "max" not in line:
        GB_mem_time = float(line.split()[1])
        jobs[job_id][task_id]["mem"] = GB_mem_time
        jobs[job_id][task_id]["mem_kWh"] = calc_mem_kWh(GB_mem_time)
        jobs[job_id][task_id]["mem_gCO2"] = calc_carbon_UK_in_g(jobs[job_id][task_id]["mem_kWh"])

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
       
#Iterate through the calculated results and print to std.out the results. We iterate over jobs and task IDs.
for job_id in jobs.keys():
    print("Job ID: "+ job_id)

    #Iterates over each task that corresponds to a given job, prints the task ID.
    for taskid in jobs[job_id].keys():
        print("\t"+str(taskid)+": ")

        #Calculates the total energy use and estimated emissions using values calculated above. Prints these values.
        jobs[job_id][taskid]["kWh"] = jobs[job_id][taskid]["cpu_kWh"]+jobs[job_id][taskid]["mem_kWh"]
        jobs[job_id][taskid]["gCO2"] = jobs[job_id][taskid]["cpu_gCO2"]+jobs[job_id][taskid]["mem_gCO2"]
        print("\t\t kWh: {:4f}".format(jobs[job_id][taskid]["kWh"]))
        print("\t\t gCO2: {:4f}".format(jobs[job_id][taskid]["gCO2"]))

        #Calculates the requested/blocked energy of cores and RAM. Blocked resources prevent other jobs running,
        #and should be included in emissions due to the cost of these resources even if not used.
        jobs[job_id][taskid]["kWh_req"] = calc_job_req_kWh(
                                                cpu_info[node_info[jobs[job_id][taskid]["host"]]],
                                                jobs[job_id][taskid]["NUM_CPU"],
                                                jobs[job_id][taskid]["wallclock"],
                                                jobs[job_id][taskid]["RAM"])
        print("\t\t kWh Requested: {:4f}".format(jobs[job_id][taskid]["kWh_req"]))
        jobs[job_id][taskid]["gCO2_req"] = calc_carbon_UK_in_g(jobs[job_id][taskid]["kWh_req"])
        print("\t\t gCO2 Requested: {:4f}".format(jobs[job_id][taskid]["gCO2_req"]))      

#Creates an output JSON file for this job and writes the calculated information into it.
with open("Job_JSONs/calc_carbon_"+str(job_id)+".json","w") as fout:
    json.dump(jobs,fout,indent=2)