import os,sys
from datetime import datetime
import json
import subprocess
import gzip

jobs = {}
destinations = {}
log_data = []
settings = {}
path_temp = ""

def run_jobs():
	global destinations,path_temp
    
    # cleanup 
    if clean_up()== 0:
        log("INFO","admin","Cleaning up temp directory.") 
        
	for job in jobs:
		job_name = job['name']
		log("INFO", job_name,"Starting backup.") 
		destiny = return_array(job['destinations'])
		if len(destiny)==0:
			log("WARN",job_name,"Job has no destination, skipping...")
			continue 
		path_temp = settings['temp'].strip() 
		if path_temp[-1] != '/':
			path_temp = path_temp+'/'
		
		# compress paths
		if "path" in job:
            compress_paths(job)	
			
		
		# Process docker
		if "docker" in job:
            compress_docker(job)
		
        # upload compressed files to backup servers
        upload_files(job)
        	
		# cleanup
		if clean_up() == 0:
            log("INFO",job_name,"All cleaned up, job finished.") 	

					
def compress_paths(job):
	paths = return_array(job["path"])
	for path in paths:
		log("INFO",job_name,"Compressing "+path)
		path_stamp = path.replace('/','-') 
	
		p,output,err = exec_command(['tar','cpfz',path_temp+job_name+path_stamp+'-'+datestamp()+'.tar.gz',path],False) 
		if p ==1: 
			log("WARN",job_name,"Exit "+str(p)+" - "+err)
		elif p==0:
			log("INFO",job_name,"Compression successfull.")
		else:
			log("FAULT",job_name,"Exit "+str(p)+" - "+err);

def compress_docker(job):
	dockers = return_array(job["docker"]) 
	for docker in dockers:
		container = ""

		# get the container name
		p,output,err = exec_command(["docker", "inspect", "--format", "'{{.Name}}'",docker], False)
		if p == 0:
			container = str(output)[2:-2]
			log("INFO",job_name,"Starting dumping of docker container "+container)
		else:
			log("WARN",job_name,"Container "+docker+" doesn't seem to exist. Skipping...")
			continue 

		# save the container as an image
		log("INFO",job_name,"Creating image of container "+container)
		dest_cont = job_name+"-docker-"+container+"-"+datestamp()
		p,output,err = exec_command(["docker","commit","-p",docker,dest_cont],False)
		if p != 0:
			log("WARN",job_name,"Container "+container+" couldn't be saved as an image.") 
			continue
		
		# compress docker image
		# Needs to find a better way to compress the image, as well as get rid of "shell=True"
		log("INFO",job_name,"Compressing image.")
		tar_docker = ["docker","save", dest_cont]
		gzip_docker = ["gzip",">",path_temp+dest_cont+".tar.gz"]
		try: 
			p = subprocess.check_output("docker save "+dest_cont+" | gzip > "+path_temp+dest_cont+".tar.gz",shell=True)
		except subprocess.CalledProcessError as grepexc:
			if grepexc.returncode == 0: 	
				log("INFO",job_name,"Docker container "+container+" successfully compressed.")
			else:
				log("FAULT",job_name,"Compressing the container "+container+" has failed.")

		# erase image
		p,output,err = exec_command(["docker","rmi",dest_cont],False)
		if p == 0:
			log("INFO",job_name,"Image of container "+container+" was successfully removed.")
		else:
			log("FAULT",job_name,"Image of container "+container+" wasn't removed!")
        

def upload_files(job):
    destiny = return_array(job['destinations'])
	# transfer files to remote servers
	for destination in destiny:
		dest = {}
		for d in destinations:
			if d["name"] == destination:
				dest = d
				log("INFO",job_name,"Starting to upload files to remote server: "+dest["address"]) 
				command = ["scp"] 
				if "key" in dest:
					command.extend(["-i",dest["key"]])
				if "port" in dest:
					command.extend(["-P",dest["port"]])
				command.extend([path_temp+"*",dest["address"]+"/"+job_name])
				command = [ x.encode("ascii") for x in command ]
				p = ""
				try:
					p = subprocess.check_output(" ".join(command),shell = True)
				except subprocess.CalledProcessError as grepexc:
                                    	if grepexc.returncode == 0:
						log("INFO",job_name,"Files transferred successfully! Cleaning up...")
					else:
						log("FAULT",job_name,"Transfer has failed! check your settings: "+p)

def clean_up():
	try:
		p = subprocess.check_output("rm -rf "+path_temp+"*",shell = True)
		return 0
	except subprocess.CalledProcessError as grepexc:
		if grepexc.returncode != 0:
			log("FAULT",job_name,"Failed to clean up: "+grepexc.output)    
            return grepexc.returncode

def exec_command(command, shell):
	p = subprocess.Popen(command, shell,stdout=subprocess.PIPE, stderr = subprocess.PIPE)		
	output,err = p.communicate()
	return p.returncode,output,err

def return_array(obj): 
	if isinstance(obj,list):
		return obj
	else:
		return [obj]

def log(level,job,message):
	global log_data
	loginfo = str(datetime.now()).split('.')[0]+" ["+level+"]"+" "+job+" "+message
	log_data.append(loginfo)
	with open("backups.log","a") as mylog:
		mylog.write(loginfo+'\n')
	if "-v" in sys.argv:
		print (loginfo)

def datestamp():
	fulltime = str(datetime.now())
	partialtime = ""+fulltime[0:10]+"-"+fulltime[11:16].replace(':','-') 
	return partialtime

def read_jobs(): 
	global jobs
	with open("servers.json","r") as f:
		jobs = json.load(f)	

def read_destinations():
	global destinations
	with open("destinations.json","r") as f:
		destinations = json.load(f)

def read_settings():
	global settings
	with open("settings.json","r") as f:
		settings = json.load(f)

pathname = os.path.dirname(os.path.realpath(__file__))
os.chdir(pathname)
read_jobs()
read_destinations()
read_settings()
run_jobs()
