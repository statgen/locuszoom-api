#!/usr/bin/env python
import random
import requests
import gevent
import sqlite3
import time
import colorama
from gevent import monkey
from pprint import pprint

colorama.init(autoreset=True)

# patches stdlib (including socket and ssl modules) to cooperate with other greenlets
monkey.patch_all()

# Number of simultaneous requests to try
CONCURRENT_REQUESTS = 300

# Number of requests to try in serial (if testing in serial mode)
SERIAL_REQUESTS = CONCURRENT_REQUESTS

# Region size, in bp
FLANK_SIZE = 250000

# SQLITE database with 1000G variants
G1K_DB = "/net/snowwhite/home/welchr/projects/1000g_phase3_v5/g1k_phase3_v5.sqlite"

def send_request(url,params):
  if "chrom" in params:
    params["chrom"] = params["chrom"].replace("chrom","")
  elif "chr" in params:
    params["chr"] = params["chr"].replace("chr","")

  start = time.time()
  resp = requests.get(url,params=params)
  end = time.time()

  return resp, end-start

def random_variant_in_range(chrom,start,end,db_con):
  cur = db_con.execute("SELECT * FROM g1k_phase3_v5_ALL WHERE chrom = ? AND pos > ? AND pos < ? ORDER BY RANDOM() LIMIT 1",(chrom,start,end))
  row = cur.fetchone()
  return row

def dict_factory(cursor, row):
  d = {}

  for idx, col in enumerate(cursor.description):
    d[col[0]] = row[idx]

  return d

def test_parallel():
  con = sqlite3.connect(G1K_DB)
  con.row_factory = dict_factory

  url = "http://portaldev.sph.umich.edu/flask/v1/annotation/recomb/results/"

  req_args = []
  for i in xrange(CONCURRENT_REQUESTS):
    # Pick a random chromosome.
    chrom = random.choice(xrange(1,23))

    # Pick a random range on the chromosome (just for finding a variant.)
    for i in xrange(100):
      point = random.randint(150000,100000000)
      start = point - FLANK_SIZE
      end = point + FLANK_SIZE

      # Pick a variant from that chromosome.
      random_variant = random_variant_in_range(chrom,start,end,con)

      if random_variant is not None:
        break

    if random_variant is None:
      raise Exception, "For some reason I couldn't find a variant on this chromosome {}".format(chrom)

    req_args.append({
      "filter": "chromosome in '{chrom}' and position > '{start}' and position < '{end}'".format(
        chrom = chrom,
        start = start,
        end = end
      ),
      "fields": "chromosome,position,recomb_rate"
    })

  start_asc = time.asctime()
  start = time.time()
  jobs = [gevent.spawn(send_request,url,params) for params in req_args]
  gevent.joinall(jobs)
  end = time.time()
  end_asc = time.asctime()

  for j in jobs:
    time_req = j.value[1]
    resp = j.value[0]

    try:
      print resp.status_code
      print resp.reason
      print resp.url
      print "Time required (s): {}".format(time_req)

      try:
        print "Number of items returned: {}".format(len(resp.json()["data"]["chromosome"]))
      except:
        print resp.json()

      print ""
    except:
      raise

  print "Sending {} requests at {}".format(len(req_args),start_asc)
  print "Finished at {}".format(end_asc)
  print "Seconds required: {}".format(round(end-start,2))

  return jobs

if __name__ == "__main__":
  jobs = test_parallel()

