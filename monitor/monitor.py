#!/usr/bin/env python
from __future__ import print_function
from multiprocessing import Process
from urllib.parse import urlparse
from termcolor import colored
import os, sys, psutil, time, requests

INTERVAL_TIME = 30 # seconds
with open("webhook") as fp:
  WEBHOOK_URL = fp.read().strip()

API_TEST_URLS = [
  "http://portaldev.sph.umich.edu/api/v1/annotation/recomb/results/?filter=id in 15 and chromosome eq '7' and position le 28496413 and position ge 27896413",
  "http://portaldev.sph.umich.edu/api/v1/annotation/genes/?filter=source in 2 and chrom eq '7' and start le 28496413 and end ge 27896413",
  "http://portaldev.sph.umich.edu/api/v1/pair/LD/results/?filter=reference eq 1 and chromosome2 eq '7' and position2 ge 27896413 and position2 le 28496413 and variant1 eq '7:28180556_T/C'"
]

def is_flask(proc):
  try:
    return ("PORTALAPI_MODE" in proc.environ()) and (len(proc.children()) > 0)
  except:
    return False

def get_process(pid):
  try:
    return psutil.Process(pid=pid)
  except:
    return None

def msg_json(server,event,url=None,cwd=None,error=None):
  json = {
    "attachments": [{
      "color": "danger",
      "pretext": "An API server event occurred",
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
        p.environ()["PORTALAPI_MODE"],
        p.pid,
        p.cwd()
      )

      servers.append(s)

  return servers

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
            "api_mode": p.environ()["PORTALAPI_MODE"]
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

def monitor_api_endpoints():
  last = {}
  current = {}
  while 1:
    now = int(time.time())
    for url in API_TEST_URLS:
      print("Checking endpoint: {}".format(url))

      last.setdefault(url,{"state": True})
      parsed = urlparse(url)

      api_mode = None
      if parsed.path.startswith("/api_internal_dev"):
        api_mode = "dev"
      elif parsed.path.startswith("/flaskdbg"):
        api_mode = "dev"
      elif parsed.path.startswith("/flaskquick"):
        api_mode = "quick"
      elif parsed.path.startswith("/flask"):
        api_mode = "prod"
      elif parsed.path.startswith("/api"):
        api_mode = "prod"

      timed_out = False
      try:
        resp = requests.get(url,timeout=5)
      except requests.exceptions.Timeout:
        timed_out = True

      error = "[HTTP {}]: {}".format(resp.status_code,resp.reason)

      if timed_out:
        current[url] = {"state": False,"event": "Request timed out","time": int(time.time())}
      elif not resp.ok:
        current[url] = {"state": False,"event": "Request error","time": int(time.time()),"error": error}
      else:
        current[url] = {"state": True,"event": "Request OK","time": int(time.time())}

      if last[url]["state"] and not current[url]["state"]:
        send_slack(
          api_mode,
          current[url]["event"],
          url,
          None,
          current[url]["error"]
        )

      if timed_out or not resp.ok:
        print(colored("... FAIL : {}".format(error),"red"))
      else:
        print(colored("... OK","green"))

      last[url] = current[url]

      print("")
      time.sleep(1)

    time.sleep(INTERVAL_TIME)

if __name__ == "__main__":
  proc_flask = Process(target=monitor_flask)
  proc_flask.start()

  proc_api = Process(target=monitor_api_endpoints)
  proc_api.start()

  proc_flask.join()
  proc_api.join()


