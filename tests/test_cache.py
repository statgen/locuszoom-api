#!/usr/bin/env python
import requests
import time

url = "http://portaldev.sph.umich.edu/flaskdbg/v1/statistic/pair/LD/results/?filter=reference%20eq%201%20and%20chromosome2%20eq%20%2710%27%20and%20position2%20ge%20114550452%20and%20position2%20le%20115067678%20and%20variant1%20eq%20%2710:114756041_A/T%27&fields=chr,pos,rsquare"

while 1:
  print "Firing off request..."

  start = time.time()
  resp = requests.get(url)
  end = time.time()

  print "Received LD for {} variants in {} seconds".format(
    len(resp.json()["data"]["variant2"]),
    "%0.1f" % (end - start)
  )

  time.sleep(5)

