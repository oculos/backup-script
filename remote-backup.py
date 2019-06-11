#!/usr/bin/env python
import sys
from backup import *
from backup import jobs
import backup 

def define_path(): 
	global path_temp,settings
	path_temp = settings['temp'].strip()
        if path_temp == "":
                print ("Temp directory blank. Please define a temporary directory on settings.json")
                log("FAULT","admin","Temp directory blank. Script can't run without a temp directory.")
        if path_temp[-1] != '/':
                path_temp = path_temp+'2/'
		backup.path_temp = path_temp

def run_jobs():
        global destinations,path_temp

        # cleanup
        if clean_up()== 0:
                log("INFO","admin","Cleaning up temp directory.")
        
        for job in jobs:
                job_name = job['name']
                log("INFO", job_name,"REMOTE - Starting backup.")
                
                #compress paths
                if "path" in job:
                        compress_paths(job)
 		# Process docker
                if "docker" in job:
                        compress_docker(job)


if __name__ == "__main__": 
	pathname = os.path.dirname(os.path.realpath(__file__))
        os.chdir(pathname)
	settings = read_settings()
	define_path()
        jobs = read_jobs()
        read_destinations()
	if sys.argv[1] == 'backup':
		run_jobs()
	if sys.argv[1] == 'cleanup':
		clean_up()

