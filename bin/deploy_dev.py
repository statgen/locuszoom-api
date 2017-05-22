#!/usr/bin/env python
from __future__ import print_function
import os, sys, requests, time

def bash(cmd,check=True,wait=True):
  from subprocess import Popen
  p = Popen(cmd,shell=True,executable="/bin/bash",universal_newlines=True)

  if wait:
    p.wait()

  if wait and check:
    if p.returncode != 0:
      raise Exception("Shell command `{}` failed with returncode {}".format(cmd,p.returncode))

  return p.returncode

# Dev server location
os.chdir("/home/portaldev/lzapi_dev")

# Import variables first
cfg = "etc/config-dev.py"
exec(compile(open(cfg,"rb").read(),cfg,'exec'),globals(),locals())

# Kill currently running server
print("Killing server running on port {}".format(FLASK_PORT))
killcode = bash("bin/kill_server.py --port {} --kill".format(FLASK_PORT),check=False)
if killcode not in (0,1):
  raise Exception("Script to kill server failed unexpectedly")

# Checkout
bash("git checkout dev && git pull")

# Activate environment and run server
print("Starting development server")
bash("source venv/bin/activate && bin/run_gunicorn.py dev",wait=False)

# Give the server reasonable amount of time to startup
time.sleep(5)

# Smoke test
testreq = requests.get("http://localhost:{}/v1/statistic/single/".format(FLASK_PORT))
if testreq.status_code != 200:
  raise Exception("Development server failed smoke test; not returning data for /v1/statistic/single/")

