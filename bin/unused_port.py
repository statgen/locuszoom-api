#!/usr/bin/env python
from __future__ import print_function
import psutil, random

used_ports = set([x.laddr[1] for x in psutil.net_connections()])
while 1:
  port = random.randint(1024,65535)
  if port not in used_ports:
    print(port)
    break

