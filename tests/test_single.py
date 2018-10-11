import requests, os, pytest

@pytest.fixture
def port():
  return os.environ["FLASK_PORT"]

@pytest.fixture
def host():
  return os.environ["FLASK_HOST"]

def test_statistic_single(host,port):
  resp = requests.get("http://{}:{}/v1/statistic/single/".format(host,port))
  assert resp.ok

  data = resp.json()
  for k in "analysis build date first_author last_author id imputed pmid study tech trait".split():
    assert k in data["data"]
    assert len(data["data"][k]) > 1

