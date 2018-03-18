import requests, os, pytest

@pytest.fixture
def port():
  return os.environ["FLASK_PORT"]

@pytest.fixture
def host():
  return os.environ["FLASK_HOST"]

def test_annotation_gwascatalog(host,port):
  # Check metadata endpoint
  resp = requests.get("http://{}:{}/v1/annotation/gwascatalog/".format(host,port))
  assert resp.ok

  data = resp.json()
  for k in "id name genome_build date_inserted catalog_version".split():
    assert k in data["data"]
    assert len(data["data"][k]) > 1

  # Check results endpoint
  test_id = data["data"]["id"][0]
  params = {
    "filter": "id in {} and rsid eq 'rs7903146'".format(test_id),
    "limit": 1,
    "sort": "pos"
  }
  results = requests.get("http://{}:{}/v1/annotation/gwascatalog/results/".format(host,port),params=params)

  assert results.ok

  result_data = results.json()
  assert "data" in result_data
  assert len(result_data["data"]) > 0

  for k in "id variant rsid chrom pos ref alt trait trait_group risk_allele risk_frq log_pvalue or_beta genes pmid pubdate first_author study".split():
    assert k in result_data["data"]

