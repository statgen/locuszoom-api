#!/usr/bin/env python
from __future__ import print_function
import os, sys, psutil, time

# THIS SCRIPT SHOULD BE RUN AS ROOT

def is_flask(proc):
  try:
    return "LZAPI_MODE" in proc.environ() and len(proc.children()) > 0 and proc.name() == "gunicorn"
  except:
    return False

def get_process(pid):
  try:
    return psutil.Process(pid=pid)
  except:
    return None

class FlaskServerInfo(object):
  def __init__(self,mode,pid,ppid,cwd,cons):
    self.mode = mode
    self.pid = pid
    self.ppid = ppid
    self.cwd = cwd
    self.cons = cons

  def __str__(self):
    constrings = []
    for c in self.cons:
      if c.status == "LISTEN":
        constrings.append("Listening on {} to port {}".format(*(c.laddr)))

    template = """
      Server: {0.mode}
      Working directory: {0.cwd}
      PID: {0.pid}
      {1}
    """

    template = "\n".join([x.lstrip() for x in template.strip().split("\n")])
    return template.format(self,"\n".join(constrings))

def find_flask_servers():
  servers = []
  for p in psutil.process_iter():
    if is_flask(p):
      s = FlaskServerInfo(
        p.environ()["LZAPI_MODE"],
        p.pid,
        p.ppid(),
        p.cwd(),
        p.connections()
      )

      servers.append(s)

  return servers

if __name__ == "__main__":
  servers = find_flask_servers()
  for s in servers:
    print(s)
    print()

