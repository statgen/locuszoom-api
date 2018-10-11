#!/usr/bin/env python3

from multiprocessing import Process
from urllib.parse import urlparse
from termcolor import colored
import os, sys, psutil, time, requests
from signal import signal, SIGTERM, SIGINT
import atexit
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from glob import glob

# This script is meant to execute on a remote/external machine to monitor
# the status of the API servers. 

# How often to poll/check up on things?
INTERVAL_TIME = 30 # seconds

with open("webhook") as fp:
  WEBHOOK_URL = fp.read().strip()

API_TEST_URLS = [
  "http://portaldev.sph.umich.edu/api/v1/annotation/recomb/results/?filter=id in 15 and chromosome eq '7' and position le 28496413 and position ge 27896413",
  "http://portaldev.sph.umich.edu/api/v1/annotation/genes/?filter=source in 2 and chrom eq '7' and start le 28496413 and end ge 27896413",
  "http://portaldev.sph.umich.edu/api/v1/pair/LD/results/?filter=reference eq 1 and chromosome2 eq '7' and position2 ge 27896413 and position2 le 28496413 and variant1 eq '7:28180556_T/C'",
  "http://portaldev.sph.umich.edu/api/v1/annotation/intervals/results/?filter=id in 16 and chromosome eq '2' and start < 24200"
]

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
        current[url] = {"state": False,"event": "Request timed out","time": int(time.time()),"error": error}
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
  proc_api = Process(target=monitor_api_endpoints)
  proc_api.start()
  proc_api.join()

