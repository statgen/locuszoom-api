import requests, os, pytest

@pytest.fixture
def port():
  return os.environ["FLASK_PORT"]

@pytest.fixture
def host():
  return os.environ["FLASK_HOST"]

def test_invalid_op(host,port):
  params = {
    "filter": "trait is 'BMI'"
  }
  resp = requests.get("http://{}:{}/v1/statistic/single/".format(host,port),params=params)
  assert resp.status_code == 400
  data = resp.json()
  assert "Incorrect syntax" in data["message"]

