#!/usr/bin/env python
import os, sys, time, traceback
import requests
from colored import fg, attr as colattr
from pprint import pprint
from collections import OrderedDict

def print_depth(json,depth=2,truncate=50):
  """
  Print only `depth` number of levels in a JSON object.
  At max(depth), print values, but truncated to fit within `truncate` characters.
  """
  pass

base_url = "http://localhost/flaskdbg/v1/"

urls = [
  # "http://localhost:11111/v1/single/",
  # "http://localhost:11111/v1/single/?filter=analysis in 1",
  base_url + "single/results/?filter=analysis in 1 and chromosome in '1' and position ge 10000 and position le 20000",
  # "http://localhost:11111/v1/annotation/genes/sources/",
  # "http://localhost:11111/v1/annotation/genes/?filter=source in 1 and chrom eq '20' and start ge 2000000 and end le 2100000",
  # "http://localhost:11111/v1/pair/LD/",
  # "http://localhost:11111/v1/pair/LD/results/?filter=reference eq 1 and chromosome2 eq '9' and position2 ge 16961 and position2 le 16967 and variant1 eq '9:16918_G/C'&fields=chr,pos,rsquare",
  #"http://localhost:11111/v1/annotation/intervals/"
  base_url + 'annotation/intervals/',
  base_url + 'annotation/intervals/?sort=version',
  base_url + 'annotation/intervals/results/?filter=id in 16 and chromosome eq "2" and start < 24200&sort=end',
  base_url + 'annotation/recomb/results/?filter=id in 15 and chromosome eq "21" and pos lt 10906989',
  base_url + 'annotation/recomb/?format=objects',
  base_url + "statistic/pair/LD/results/?filter=reference eq 1 and chromosome2 eq '10' and position2 ge 114553452 and position2 le 114555452 and variant1 eq '10:114756041_A/T'"
]

while 1:
  for u in urls:
    print u

    try:
      resp = requests.get(u)
    except:
      print traceback.print_exc()
      time.sleep(3)
      continue

    print time.ctime()
    if resp.ok:
      print pprint(resp.json())
      print >> sys.stderr, "%sQuery OK%s" % (fg("green"),colattr("reset"))
    else:
      print >> sys.stderr, "%sQuery failed:%s %s, reason: [%i] %s" % (fg(1),colattr("reset"),u,resp.ok,resp.reason)

    print ""

  # time.sleep(5)
  break

