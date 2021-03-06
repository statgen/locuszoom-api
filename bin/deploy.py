#!/usr/bin/env python3
import os, sys, requests, time, psutil, signal
from getpass import getuser

def find_server(api_mode):
  for p in psutil.process_iter():
    try:
      if p.name() == "gunicorn" and p.environ()["LZAPI_MODE"] == api_mode:
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

def bash(cmd,check=True,wait=True,echo=True):
  from subprocess import Popen

  if echo:
    print(cmd)

  p = Popen(cmd,shell=True,executable="/bin/bash",universal_newlines=True)

  if wait:
    p.wait()

  if wait and check:
    if p.returncode != 0:
      raise Exception("Shell command `{}` failed with returncode {}".format(cmd,p.returncode))

  return p.returncode

if __name__ == "__main__":
  # Get the API mode
  LZAPI_MODE = os.environ.get("LZAPI_MODE")
  if LZAPI_MODE is None:
    try:
      LZAPI_MODE = sys.argv[1]
    except:
      raise ValueError("Must set LZAPI_MODE or pass it as first argument")

  LZAPI_HOME = os.environ.get("LZAPI_HOME")
  CFG = f"etc/config-{LZAPI_MODE}.py"

  if LZAPI_HOME is not None:
    os.chdir(LZAPI_HOME)

  # Check for config file.
  # This also serves as a check that we are running from the proper working directory.
  if not os.path.isfile(CFG):
    raise ValueError(f"Could not find config {CFG}. Make sure you are executing this script at the root of the API home directory or set LZAPI_HOME.")

  # Import variables from config file, including:
  # API_VERSION
  # API_BRANCH
  # FLASK_HOST
  # FLASK_PORT
  print(f"Loading config: {CFG}")
  exec(compile(open(CFG,"rb").read(),CFG,'exec'),globals(),locals())

  # Check we are running as correct user
  if getuser() != API_USER:
    raise ValueError(f"Must run deploy script as user {API_USER}")

  # Kill currently running server
  print(f"Killing current {LZAPI_MODE} server")
  pid = find_server(LZAPI_MODE)
  if pid is not None:
    print(f"... server PID {pid} will be killed")
    kill_server(pid)
  else:
    print(f"... no existing API server running for mode {LZAPI_MODE}")

  # Checkout
  bash(f"git fetch && git reset --hard origin/{API_BRANCH}")

  # Setup venv
  bash("rm -rf venv")
  pyexe = sys.executable
  bash(f"{pyexe} -m virtualenv --no-site-packages venv")

  # For some reason psycopg2 is special and must be separately installed & forcibly reinstalled or you'll get libpq errors
  bash("source venv/bin/activate && pip install -e .")

  # Activate environment and run server
  print("Starting server")
  bash(f"source venv/bin/activate && bin/run_gunicorn.py",wait=False)

  # Give the server reasonable amount of time to startup
  time.sleep(5)

  # Smoke test
  url = "http://localhost:{}/v1/statistic/single/".format(FLASK_PORT)
  print(f"Running smoke test against {url}")
  testreq = requests.get(url)
  if testreq.status_code != 200:
    raise Exception("... API server failed smoke test!")

  print("Deployment finished")
