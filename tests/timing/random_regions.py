#!/usr/bin/env python3
import random

chroms = [['1', 249250621],
          ['2', 243199373],
          ['3', 198022430],
          ['4', 191154276],
          ['5', 180915260],
          ['6', 171115067],
          ['7', 159138663],
          ['8', 146364022],
          ['9', 141213431],
          ['10', 135534747],
          ['11', 135006516],
          ['12', 133851895],
          ['13', 115169878],
          ['14', 107349540],
          ['15', 102531392],
          ['16', 90354753],
          ['17', 81195210],
          ['18', 78077248],
          ['19', 59128983],
          ['20', 63025520],
          ['21', 48129895],
          ['22', 51304566],
          # ['X', 155270560],
          # ['Y', 59373566],
         ]

def random_region(size=500000):
  chrom = random.choice(chroms)
  while 1:
    start = random.randint(1, chrom[1])
    end = start + size
    if end < chrom[1]:
      break

  return chrom[0], start, end

def format_region(chrom, start, end):
  return f"{chrom}:{start}-{end}"

for _ in range(1000):
  print(format_region(*random_region()))
