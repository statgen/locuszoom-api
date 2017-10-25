#!/usr/bin/env python
from __future__ import print_function
import os, sys, requests, time, psutil, signal

API_HOME = "/home/portaldev/lzapi_dev"
CFG = "etc/config-dev.py"

def find_server():
  for p in psutil.process_iter():
    try:
      if p.name() == "gunicorn" and p.cwd() == API_HOME:
        return p.pid
    except:
      pass

def process_exists(pid):
  try:
    psutil.Process(pid)
    return True
  except:
    return False

def kill_server(pid,timeout=3):
  """
  Try to kill a process by PID with SIGTERM.
  If it still exists after X seconds, SIGKILL it.
  """

  os.kill(pid,signal.SIGTERM)
  time.sleep(timeout)

  if process_exists(pid):
    os.kill(pid,signal.SIGKILL)

  time.sleep(timeout)

  if process_exists(pid):
    raise Exception("Unable to kill server process at PID " + str(pid))

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
os.chdir(API_HOME)

# Import variables first
exec(compile(open(CFG,"rb").read(),CFG,'exec'),globals(),locals())

# Kill currently running server
pid = find_server()
if pid is not None:
  kill_server(pid)

# Checkout
bash("git fetch && git reset --hard origin/dev")

# Setup venv
bash("rm -rf venv")
bash("python -m virtualenv --no-site-packages venv")
bash("source venv/bin/activate && pip install -r requirements.txt")

# Activate environment and run server
print("Starting development server")
bash("source venv/bin/activate && bin/run_gunicorn.py dev",wait=False)

# Give the server reasonable amount of time to startup
time.sleep(5)

# Smoke test
testreq = requests.get("http://localhost:{}/v1/statistic/single/".format(FLASK_PORT))
if testreq.status_code != 200:
  raise Exception("Development server failed smoke test; not returning data for /v1/statistic/single/")

