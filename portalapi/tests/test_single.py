import requests, os, pytest

@pytest.fixture
def port():
  return os.environ["FLASK_PORT"]

@pytest.fixture
def host():
  return os.environ["FLASK_HOST"]

def test_statistic_single(host,port):
  resp = requests.get("http://{}:{}/v1/statistic/single".format(host,port))
  assert resp.ok

  data = resp.json()
  assert len(data["data"]["id"]) > 1

