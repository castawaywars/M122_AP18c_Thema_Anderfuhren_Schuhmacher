import time
import os
import inspect
import subprocess

print("Greetings, this is your friendly neighbourhood virus.")
print("To stop me, close this terminal before I print the 'proceeding' message.")
time.sleep(1)
print("proceeding")

filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))
print(filename)
print(path)


filestring=str(filename)

filestring='"'+filestring+'"'

print(filestring)

subprocess.call("start python "+filestring, shell=True)

#os.system(filename)

#exec(open(filename).read())

print("end of instance")
