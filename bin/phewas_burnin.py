#!/usr/bin/env python3
import random
import gzip
import requests
import time

API_URL = "http://{host}:{port}/v1/statistic/phewas/"

VARIANTS = """
9:14775208_A/G
15:78095685_G/A
17:65313386_C/T
20:49782767_C/G
6:33932611_A/G
3:102896629_T/C
2:118086982_A/G
2:208978677_C/T
9:8390505_A/G
11:27065746_G/A
18:71594668_A/T
1:107985531_G/A
22:23990354_C/T
19:7858901_T/C
4:154810957_T/A
8:18779787_T/C
11:134857066_G/A
1:143240722_G/T
15:61622539_G/C
10:56607505_T/C
8:142684336_C/T
11:93179153_C/A
3:23496500_G/A
1:20624128_G/A
19:19982060_T/C
7:16096507_T/A
8:88100466_T/C
19:44049881_G/T
14:27835455_T/C
6:19582739_A/G
4:119961513_G/A
19:58858036_G/C
13:107734581_A/T
7:26877565_A/G
15:94203466_C/T
3:161206225_T/C
2:191056469_A/G
8:64086044_G/A
2:182406668_A/G
13:79623535_G/A
4:108000868_C/G
10:120764293_G/T
2:66385822_C/T
2:155563062_C/T
4:121855304_C/T
8:48317938_G/A
6:23284226_C/T
13:43577982_T/C
3:154526737_A/G
13:104209182_C/T
9:126175024_T/C
7:73094584_T/G
3:4205648_A/C
5:141294684_C/A
12:61514494_C/T
10:131641704_G/A
10:123462129_G/A
6:133191055_G/A
3:185846813_G/T
6:36879275_T/A
18:26548839_T/C
6:16187971_C/T
6:73438784_T/C
2:241453450_C/T
11:23789456_G/A
10:120176978_A/G
9:93557381_G/C
17:72302252_G/A
21:39580114_C/T
10:29895704_G/A
7:9864360_T/G
2:226581223_G/T
7:118537326_G/A
12:69833486_T/C
2:77603507_A/G
13:104143516_T/C
2:55126109_C/T
10:58735521_G/T
5:177396364_G/A
6:70135959_G/A
5:132261693_G/A
4:77751351_G/A
10:9071002_T/C
4:58966288_T/A
1:233877514_C/G
2:69464833_A/G
2:126377717_A/G
15:79326001_G/A
3:57707136_T/C
1:160351594_T/C
2:154874460_G/A
4:34456132_A/G
7:11031504_C/T
16:83208749_A/G
8:71871428_T/C
7:16594454_T/C
2:206733638_C/T
11:49471862_G/A
15:36717941_A/C
6:83249741_C/T
""".split()

class Timer:
  def __enter__(self):
    self.s = time.time()
    return self

  def __exit__(self,*args,**kwargs):
    self.e = time.time()
    self.elapsed = self.e - self.s

def get_settings():
  from argparse import ArgumentParser
  p = ArgumentParser()
  p.add_argument("--port",type=int,default="7000")
  p.add_argument("--host",type=str,default="localhost")
  p.add_argument("--wait",type=int,default=0,help="Amount of time to wait between requests. Default is 0 seconds (no wait).")
  return p.parse_args()

if __name__ == "__main__":
  args = get_settings()

  if args.port < 0 or args.port > 65535:
    raise ValueError(f"Invalid port {args.port}")

  while 1:
    sample = [random.choice(VARIANTS) for _ in range(100)]
    url = API_URL.format(host=args.host,port=args.port)
    for v in sample:
      print(f"Variant {v}")
      for i in range(3):
        time.sleep(args.wait + 0.01)
        with Timer() as t:
          try:
            resp = requests.get(url,params={"filter": f"variant eq '{v}'","format": "objects","build": "GRCh37"})
          except:
            print(f"Query {i} failed")
            continue

          if not resp.ok:
            print(f"Query {i} failed")

        size = len(resp.content) / 1000.0
        print(f"Query {i} required {t.elapsed} and returned {size} KB")
