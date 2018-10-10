import requests, os, pytest

@pytest.fixture
def port():
  return os.environ["FLASK_PORT"]

@pytest.fixture
def host():
  return os.environ["FLASK_HOST"]

def test_annotation_snps(host,port):
  resp = requests.get("http://{}:{}/v1/annotation/snps/".format(host,port))
  assert resp.ok

  data = resp.json()
  assert len(data["data"]["id"]) >= 1

  test_id = data["data"]["id"][0]
  params = {
    # Every dbSNP version under the sun should contain rs7903146
    "filter": "id eq {} and rsid eq 'rs7903146'".format(test_id)
  }
  results = requests.get("http://{}:{}/v1/annotation/snps/results/".format(host,port),params=params)

  assert results.ok
  result_data = results.json()

  assert "data" in result_data
  assert len(result_data["data"]) > 0

  for k in ("alt","chromosome","id","pos","ref","rsid"):
    assert k in result_data["data"]

  # All columns should have the same length
  assert len(set(map(len,result_data["data"].values()))) == 1

