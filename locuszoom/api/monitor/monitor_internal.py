#!/usr/bin/env python3
from __future__ import print_function
from multiprocessing import Process
from urllib.parse import urlparse
from termcolor import colored
import os, sys, psutil, time, requests
from signal import signal, SIGTERM, SIGINT
import atexit
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from glob import glob

# This script is meant to be run on the same machine as the API servers.

PGPASS = os.path.expanduser("~/.pgpass")
if not os.path.isfile(PGPASS):
  raise IOError("You must have a pgpass file to initiate database connections, usually stored in ~/.pgpass")

def whereami():
  import sys
  from os import path
  from socket import gethostname

  if "monitor.py" in sys.argv[0]:
    here = path.dirname(path.abspath(sys.argv[0]))
  else:
    here = os.getcwd()

  return here

# Load configurations
configs = {}
cfg_paths = glob(os.path.join(whereami(),"../../etc/config-*py"))
for p in cfg_paths:
  loc = {}
  with open(p) as f:
    code = compile(f.read(), p, 'exec')
    exec(code,loc)

  key = os.path.basename(p).replace(".py","")
  configs[key] = loc

# If number of database connections exceeds this number, send warning.
CON_COUNT_WARN = 250

# How often to poll/check up on things?
INTERVAL_TIME = 30 # seconds

with open("webhook") as fp:
  WEBHOOK_URL = fp.read().strip()

def is_flask(proc):
  try:
    return ("LZAPI_MODE" in proc.environ()) and (len(proc.children()) > 0)
  except:
    return False

def get_process(pid):
  try:
    return psutil.Process(pid=pid)
  except:
    return None

def msg_json(server,event,url=None,cwd=None,error=None,color="danger"):
  json = {
    "attachments": [{
      "color": color,
      "pretext": "API/database monitor event",
      "fallback": "{} / {} / {}".format(server,event,error if error else ""),
      "fields": [
        {
          "title": "Server",
          "value": server,
          "short": True
        },
        {
          "title": "Event",
          "value": event,
          "short": True
        }
      ],
      "ts": int(time.time())
    }]
  }

  if cwd is not None:
    json["attachments"][0]["fields"].append({
      "title": "Working Directory",
      "value": cwd,
      "short": False
    })

  if url is not None:
    json["attachments"][0]["fields"].append({
      "title": "Request",
      "value": url,
      "short": False
    })

  if error is not None:
    json["attachments"][0]["fields"].append({
      "title": "Error",
      "value": error,
      "short": False
    })

  return json

def send_slack(*args,**kwargs):
  requests.post(WEBHOOK_URL,json=msg_json(*args,**kwargs))

def end(*args,**kwargs):
  if len(args) == 2 and hasattr(args[1],"f_trace"):
    sys.exit("Terminated by signal " + str(args[0]))
  else:
    send_slack("Monitor","Monitor was terminated")

atexit.register(end)
signal(SIGTERM,end)
signal(SIGINT,end)

class FlaskServerInfo(object):
  def __init__(self,mode,pid,cwd):
    self.mode = mode
    self.pid = pid
    self.cwd = cwd

def find_flask_servers():
  servers = []
  for p in psutil.process_iter():
    if is_flask(p):
      s = FlaskServerInfo(
        p.environ()["LZAPI_MODE"],
        p.pid,
        p.cwd()
      )

      servers.append(s)

  return servers

def monitor_database(configs):
  if not os.path.isfile(PGPASS):
    raise IOError("File does not exist or cannot access: {}".format(PGPASS))

  admin_pass = None
  with open(PGPASS,"rt") as fp:
    for line in fp:
      host, port, database, user, passwd = line.strip().split(":")
      if host.startswith("portaldev") and user == "admin":
        print("Found admin password from pgpass")
        admin_pass = passwd
        break

  history = {}
  while 1:
    for config in configs.values():
      db_name = config["DATABASE"]["database"]
      history.setdefault(db_name,{"time": 0,"count": 0})

      print("Checking database connections for '{}'...".format(db_name))

      db_url = URL(
        "postgres",
        "admin",
        admin_pass,
        config["DATABASE"]["host"],
        config["DATABASE"]["port"],
        db_name
      )

      engine = create_engine(db_url,isolation_level="AUTOCOMMIT")

      max_con = int(engine.execute("SHOW max_connections").fetchone()[0])
      connection_count = int(engine.execute("select count(*) from pg_stat_activity").fetchone()[0])
      if connection_count > CON_COUNT_WARN and history[db_name]["count"] <= CON_COUNT_WARN:
        # Previously the connection count was OK, now it's bad. Notify.
        send_slack(
          "Postgres ({})".format(db_name),
          "Large number of DB connections",
          error="Database currently has {} connections out max {}".format(connection_count,max_con),
          color="warning"
        )

      history[db_name]["count"] = connection_count

    time.sleep(INTERVAL_TIME)

def monitor_flask():
  procs = {}
  while 1:
    # Find flask instances
    for p in psutil.process_iter():
      if is_flask(p):
        cmdline = " ".join(p.cmdline())

        # Create a unique hash to represent this particular running instance of the flask.
        server_hash = "{}__{}__{}".format(
          cmdline,
          str(p.create_time()),
          str(p.pid)
        )

        if server_hash not in procs:
          # We've never seen this one before. Remember it.
          print("Found process: ({}) {}".format(p.pid,cmdline),"\n")
          procs[server_hash] = {
            "pid": p.pid,
            "cmdline": cmdline,
            "cwd": p.cwd(),
            "api_mode": p.environ()["LZAPI_MODE"]
          }

    # Now check all flask instances that we're aware of
    for shash in list(procs.keys()):
      pdata = procs[shash]
      pid = pdata["pid"]
      cmdline = pdata["cmdline"]

      proc = get_process(pid)
      if proc is None:
        print("Process died: ({}) {}".format(pid,cmdline),"\n")

        # It died. :(
        send_slack(
          pdata["api_mode"],
          "Server went down",
          None,
          pdata["cwd"]
        )

        del procs[shash]

    time.sleep(INTERVAL_TIME)

if __name__ == "__main__":
  proc_flask = Process(target=monitor_flask)
  proc_flask.start()

  proc_db = Process(target=monitor_database,args=(configs,))
  proc_db.start()

  proc_flask.join()
  proc_db.join()

