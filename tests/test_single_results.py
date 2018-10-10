import requests, os, pytest

@pytest.fixture
def port():
  return os.environ["FLASK_PORT"]

@pytest.fixture
def host():
  return os.environ["FLASK_HOST"]

def test_statistic_single_results(host,port):
  resp = requests.get("http://{}:{}/v1/statistic/single".format(host,port))
  assert resp.ok

  data = resp.json()
  assert len(data["data"]["id"]) > 1

  test_id = data["data"]["id"][0]
  params = {
    "filter": "analysis in {} and chromosome in '16' and position ge 0 and position le 200000000".format(test_id),
    "limit": 1,
    "sort": "position"
  }
  results = requests.get("http://{}:{}/v1/statistic/single/results/".format(host,port),params=params)

  assert results.ok
  result_data = results.json()
  assert "data" in result_data
  assert len(result_data["data"]) > 0
  for k in ("analysis","chromosome","log_pvalue","position","ref_allele","ref_allele_freq","score_test_stat","variant"):
    assert k in result_data["data"]

def test_empty_region(host,port):
  params = {
    "filter": "analysis in 45 and chromosome in '2' and position ge 242023897 and position le 242025881"
  }

  results = requests.get("http://{}:{}/v1/statistic/single/results/".format(host,port),params=params)
  assert results.ok

  data = results.json()["data"]
  for k in ("analysis","chromosome","log_pvalue","position","ref_allele","ref_allele_freq","score_test_stat","variant","beta","se"):
    assert k in data
    assert isinstance(data[k],list)
    assert len(data[k]) == 0

