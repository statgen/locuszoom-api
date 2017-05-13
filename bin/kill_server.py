#!/usr/bin/env python
from __future__ import print_function
import os, sys, psutil, time, argparse, signal

def find_server(port):
  port = int(port)
  for p in psutil.process_iter():
    try:
      for net in p.connections():
        if net.laddr[1] == port:
          return p.pid
    except:
      continue

def get_args():
  from argparse import ArgumentParser
  p = ArgumentParser()
  p.add_argument("--port",help="Find the server running on the given port",required=True)
  p.add_argument("--kill",help="Kill the server instead of just printing PID",default=False,action="store_true")
  return p.parse_args()

if __name__ == "__main__":
  args = get_args()
  pid = find_server(args.port)

  if pid is None:
    raise Exception("Could not find a process attached to port {}".format(args.port))

  if not args.kill:
    print(find_server(args.port))
  else:
    os.kill(int(pid),signal.SIGTERM)

