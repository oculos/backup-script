# backup-script
Python script for automatization of system backups, compression of directories, docker containers and uploading via scp.

I would like to automate the backing up of my things on VPS servers, so I wrote a script that:

- tar/compress relevant directories and/or docker containers;
- upload those compressed tars to remote servers. 

My VPS provider does not have very good solutions for incremental backups, and, while my script doesn't do incremental backups, I can fine tune what I want to backup and compress things.

There is a lot I want to add, such as better catching of exceptions, avoiding using `shell=True`, exiting graciously if the right configuration isn't present, etc. But overall the script works fine for my purposes. 

## Usage

1. Create three json files:

  - `servers.json` - this is where the folders and docker containers are supposed to be configured. Each `server` can have zero, one or multiple paths and/or docker containers for backing up.
  - `destinations.json` - this is where you configure the remote servers where your backups will be saved.
  - `settings.json` - this is where your settings go. Currently only one setting goes here (`temp`), but in the future I want to add other things so that they don't get hard-coded.
  
2. Create folders on your remote server that match the name of your "servers" that you configured on `servers.json`. 

Example: if your backup server has a folder called `backup`, and on `servers.json` you have a server called `myproject`, create a `myproject` directory inside `backup` on your remote server. The script will fail if it doesn't find a matching directory for each server configuration.

3. Create the appropriate keys for remote authentication (`ssh-keygen` and `ssh-copy-id` are your friends...;).

3. Run the script:

`python backup.py`

or for verbose mode:

`python backup.py -v`

I add `python backup.py` to my crontab so that it performs periodic backups of my stuff.

## To-do:

- checking if remote directories matching the servers to be backed up exist;
- more secure execution of shell commands (avoiding `shell=True`, better piping, optimization of saving temporary files, etc.
- better checks (ie, checking if the proper files are in place)

Any ideas on how to improve this are welcome!
