import requests, os, pytest
from six import string_types

@pytest.fixture
def port():
  return os.environ["FLASK_PORT"]

@pytest.fixture
def host():
  return os.environ["FLASK_HOST"]

def test_gene_cetp(host,port):
  params = {
    "filter": "source in 2 and chrom eq '16' and start le 57022881 and end ge 56985060"
  }
  resp = requests.get("http://{}:{}/v1/annotation/genes/".format(host,port),params=params)
  assert resp.ok

  js = resp.json()

  assert len(js["data"]) > 0

  # Check format of gene
  gene1 = js["data"][0]
  for key in ("chrom","end","exons","gene_id","gene_name","start","strand","transcripts"):
    assert key in gene1

  assert isinstance(gene1["chrom"],string_types)
  assert isinstance(gene1["end"],int)
  assert isinstance(gene1["start"],int)
  assert len(gene1["transcripts"]) > 0
  assert len(gene1["exons"]) > 0

  # CETP should be in this region
  genes = [x["gene_name"] for x in js["data"]]
  assert "CETP" in genes

  # We're on chromosome 16
  assert gene1["chrom"] == "16"

