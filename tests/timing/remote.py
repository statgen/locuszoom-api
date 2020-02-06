#!/usr/bin/env python3
import os
import re
import time
import requests
import argparse
import random

rand = random.Random(61083)

def get_settings():
  p = argparse.ArgumentParser()
  p.add_argument("--api-base", default="https://portaldev.sph.umich.edu/api/v1")
  p.add_argument("--regions", default="random_regions.txt")
  p.add_argument("--wait", default=0.75, type=float)
  p.add_argument("--verbose", default=False, action="store_true")
  p.add_argument("-n", "--num-queries", default=1000, type=int)
  args = p.parse_args()

  if not os.path.isfile(args.regions):
    raise ValueError(f"Couldn't find file '{args.regions}', specify path with `--regions <file>` or try generating first with `./random_regions.py > random_regions.txt`")

  return args

class Timer:
  def __enter__(self):
    self.s = time.time()
    return self

  def __exit__(self,*args,**kwargs):
    self.e = time.time()
    self.elapsed = self.e - self.s

def parse_region(s):
  chrom, start, end = re.search("(\d+):(\d+)-(\d+)", s).groups()
  return chrom, int(start), int(end)

def region_str(r):
  return f"{r[0]}:{r[1]}-{r[2]}"

def read_regions(fpath):
  with open(fpath) as fp:
    regions = fp.read().split()

  return [parse_region(s) for s in regions]

def request_datasets(base_url):
  resp = requests.get(base_url + "/statistic/single/", params={"format": "objects"})
  jsond = resp.json()
  return [x["id"] for x in jsond["data"]]

def statistic_single_results(base_url, dataset, region):
  query = f"?filter=analysis in {dataset} and chromosome in '{region[0]}' and position ge {region[1]} and position le {region[2]}"
  url = base_url + "/statistic/single/results/" + query
  resp = requests.get(url)
  jsond = resp.json()
  size = len(resp.content)
  return size, url, resp, jsond["data"]

def main():
  args = get_settings()
  base_url = re.sub("\/$", "", args.api_base)

  # Find available datasets.
  ids = request_datasets(base_url)

  # Read in list of random regions.
  regions = read_regions(args.regions)

  # Run queries
  for _ in range(args.num_queries):
    dataset_id = rand.choice(ids)
    region = rand.choice(regions)

    with Timer() as t:
      size, full_url, resp, data = statistic_single_results(base_url, dataset_id, region)

    print(f"Dataset {dataset_id} • Region {region_str(region)} • Time {t.elapsed:.02f}s • Size {size} • HTTP {resp.status_code}")
    if args.verbose:
      print(full_url)
      print(data)
      print("")

    time.sleep(args.wait)

if __name__ == "__main__":
  main()
