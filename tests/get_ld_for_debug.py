#!/usr/bin/env python
import requests
import pandas as pd

url = "https://portaldev.sph.umich.edu/api/v1/pair/LD/results/?filter=reference%20eq%201%20and%20chromosome2%20eq%20%278%27%20and%20position2%20ge%20118104783%20and%20position2%20le%20118264783%20and%20variant1%20eq%20%278:118184783_C/T%27&fields=chr,pos,rsquare"
resp = requests.get(url)
data = resp.json()["data"]
df = pd.DataFrame(data)

# url = "http://localhost:9000/api/v1/pair/LD/results/?filter=reference%20eq%201%20and%20chromosome2%20eq%20%278%27%20and%20position2%20ge%20118104783%20and%20position2%20le%20118264783%20and%20variant1%20eq%20%278:118184783_C/T%27&fields=chr,pos,rsquare"
# resp = requests.get(url)
# old_data = resp.json()["data"]
# old_df = pd.DataFrame(data)

