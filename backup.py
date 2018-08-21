import os,sys
from datetime import datetime
import json
import subprocess
import gzip

jobs = {}
destinations = {}
log_data = []
settings = {}
path_temp = "dummy"
def run_jobs():
        global destinations,path_temp
        
        path_temp = settings['temp'].strip()
        if path_temp == "":
                print ("Temp directory blank. Please define a temporary directory on settings.json")
                log("FAULT","admin","Temp directory blank. Script can't run without a temp directory.")
        if path_temp[-1] != '/':
                path_temp = path_temp+'/'

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
                
                #compress paths
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
        job_name = job['name']
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
        job_name = job['name']
        dockers = return_array(job["docker"])
        for docker in dockers:
                container = ""
                
                        
                # compress docker image
                # Needs to find a better way to compress the image, as well as get rid of "shell=True"

                for container in return_array(docker):
                        try:
                                log("INFO",job_name,"Stopping container...")
                                p = subprocess.check_output("docker stop "+container["name"],shell=True)
                        except subprocess.CalledProcessError as erro:
                                log("FAULT",job_name,"Failed to stop container "+container["name"]+", skipping.")
                                continue 
                        log("INFO",job_name,"Compressing data for docker container "+container["name"])
			for pth in return_array(container["paths"]):
                                try:
                                        log("INFO",job_name,"Compressing path "+pth+".")
                                        command = "docker run --rm --volumes-from "+container["name"]+" -v "+path_temp+":/backup"+ " alpine tar czf /backup/"+job_name+"-docker-"+container["name"]+pth.replace("/","-")+"-"+datestamp()+".tar.gz "+pth
                                        p = subprocess.check_output(command,shell=True)
                                except subprocess.CalledProcessError as grepexc:
                                        if grepexc.returncode == 0:
                                                log("INFO",job_name,"Docker container "+container["name"]+" volume "+pth+" sucessfully compressed.")
                                        else:
                                                log("FAULT",job_name,"Compressing the container "+container+" has failed.")
                        
                        log("INFO",job_name,"Restarting container")
                        try: 
                                p = subprocess.check_output("docker start "+container["name"],shell=True)
                        except subprocess.CalledProcessError as erro:
                                log("FAULT",job_name,"Failed to restart container.")

def upload_files(job):
        job_name = job['name']
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


