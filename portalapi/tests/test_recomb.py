import requests, os, pytest

@pytest.fixture
def port():
  return os.environ["FLASK_PORT"]

@pytest.fixture
def host():
  return os.environ["FLASK_HOST"]

def test_metadata(host,port):
  resp = requests.get("http://{}:{}/v1/annotation/recomb/".format(host,port))
  assert resp.ok

  data = resp.json()
  assert len(data["data"]["id"]) > 0

  for k in ("build","id","name","version"):
    assert k in data["data"]

  assert "lastPage" in data

def test_between_points(host,port):
  recomb_result_url = "http://{}:{}/v1/annotation/recomb/results/".format(host,port)

  # Testing interpolation when no data in between the two endpoints
  # Both endpoints should end up with the same recombination rate
  params = {
    "filter": "id in 15 and chromosome eq '21' and position lt 10890000 and position gt 10870000"
  }
  resp = requests.get(recomb_result_url,params=params)
  js = resp.json()

  assert resp.ok
  assert len(js["data"]["recomb_rate"]) == 2
  assert js["data"]["recomb_rate"][0] == js["data"]["recomb_rate"][1]

def test_overlap_1(host,port):
  recomb_result_url = "http://{}:{}/v1/annotation/recomb/results/".format(host,port)

  # Overlap only 1 recombination rate point
  # Response should have 3 values (start, known point, end)
  params = {
    "filter": "id in 15 and chromosome eq '21' and position lt 10906725 and position gt 10870000"
  }
  resp = requests.get(recomb_result_url,params=params)
  assert resp.ok
  js = resp.json()
  assert len(js["data"]["recomb_rate"]) == 3

def test_overlap_2(host,port):
  recomb_result_url = "http://{}:{}/v1/annotation/recomb/results/".format(host,port)

  # Overlap 2 recombination rate point
  # Response should have 4 values (start, 2 known points, end)
  params = {
    "filter": "id in 15 and chromosome eq '21' and position lt 10906920 and position gt 10906720"
  }
  resp = requests.get(recomb_result_url,params=params)
  assert resp.ok
  js = resp.json()
  assert len(js["data"]["recomb_rate"]) == 4

def test_no_left_data(host,port):
  recomb_result_url = "http://{}:{}/v1/annotation/recomb/results/".format(host,port)

  # Test when there is no data on the left side to use for interpolation
  params = {
    "filter": "id in 15 and chromosome eq '21' and position lt 100 and position gt 0"
  }
  resp = requests.get(recomb_result_url,params=params)
  assert resp.ok

def test_no_right_data(host,port):
  recomb_result_url = "http://{}:{}/v1/annotation/recomb/results/".format(host,port)

  # Test when there is no data on the right side to use for interpolation
  params = {
    "filter": "id in 15 and chromosome eq '21' and position lt 49000000 and position gt 48097610"
  }
  resp = requests.get(recomb_result_url,params=params)
  assert resp.ok

