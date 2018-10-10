import requests, os, pytest
from six import string_types

@pytest.fixture
def port():
  return os.environ["FLASK_PORT"]

@pytest.fixture
def host():
  return os.environ["FLASK_HOST"]

def test_omni(host,port):
  params = {
    "q": "CSF3",
    "build": "GRCh38"
  }
  resp = requests.get("http://{}:{}/v1/annotation/omnisearch/".format(host,port),params=params)
  assert resp.ok

  js = resp.json()

  assert len(js["data"]) > 0

  # Check format
  for gene in js["data"]:
    for key in ("chrom","end","gene_id","gene_name","start","term","type"):
      assert key in gene

    assert isinstance(gene["chrom"],string_types)
    assert isinstance(gene["gene_id"],string_types)
    assert isinstance(gene["gene_name"],string_types)
    assert isinstance(gene["end"],int)
    assert isinstance(gene["start"],int)

  assert isinstance(js["build"],string_types)
  assert js["build"].lower().startswith("grch")

