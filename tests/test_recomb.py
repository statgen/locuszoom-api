def test_metadata(client):
  resp = client.get("/v1/annotation/recomb/")
  assert resp.status_code == 200

  data = resp.json
  assert len(data["data"]["id"]) > 0

  for k in ("build","id","name","version"):
    assert k in data["data"]

  assert "lastPage" in data

def test_between_points(client):
  recomb_result_url = "/v1/annotation/recomb/results/"

  # Testing interpolation when no data in between the two endpoints
  # Both endpoints should end up with the same recombination rate
  params = {
    "filter": "id in 15 and chromosome eq '21' and position lt 10890000 and position gt 10870000"
  }
  resp = client.get(recomb_result_url,query_string=params)
  js = resp.json

  assert resp.status_code == 200
  assert len(js["data"]["recomb_rate"]) == 2
  assert js["data"]["recomb_rate"][0] == js["data"]["recomb_rate"][1]

def test_recommended(client):
  recomb_result_url = "/v1/annotation/recomb/results/"

  # Testing interpolation when no data in between the two endpoints
  # Both endpoints should end up with the same recombination rate
  params = {
    "filter": "chromosome eq '21' and position lt 10890000 and position gt 10870000",
    "build": "GRCh37"
  }
  resp = client.get(recomb_result_url,query_string=params)
  js = resp.json

  assert resp.status_code == 200
  assert len(js["data"]["recomb_rate"]) == 2
  assert js["data"]["recomb_rate"][0] == js["data"]["recomb_rate"][1]
  assert len(js["meta"]) > 0
  assert len(js["meta"]["datasets"]) > 0

def test_overlap_1(client):
  recomb_result_url = "/v1/annotation/recomb/results/"

  # Overlap only 1 recombination rate point
  # Response should have 3 values (start, known point, end)
  params = {
    "filter": "id in 15 and chromosome eq '21' and position lt 10906725 and position gt 10870000"
  }
  resp = client.get(recomb_result_url,query_string=params)
  assert resp.status_code == 200
  js = resp.json
  assert len(js["data"]["recomb_rate"]) == 3

def test_overlap_2(client):
  recomb_result_url = "/v1/annotation/recomb/results/"

  # Overlap 2 recombination rate point
  # Response should have 4 values (start, 2 known points, end)
  params = {
    "filter": "id in 15 and chromosome eq '21' and position lt 10906920 and position gt 10906720"
  }
  resp = client.get(recomb_result_url,query_string=params)
  assert resp.status_code == 200
  js = resp.json
  assert len(js["data"]["recomb_rate"]) == 4

def test_no_left_data(client):
  recomb_result_url = "/v1/annotation/recomb/results/"

  # Test when there is no data on the left side to use for interpolation
  params = {
    "filter": "id in 15 and chromosome eq '21' and position lt 100 and position gt 0"
  }
  resp = client.get(recomb_result_url,query_string=params)
  assert resp.status_code == 200

def test_no_right_data(client):
  recomb_result_url = "/v1/annotation/recomb/results/"

  # Test when there is no data on the right side to use for interpolation
  params = {
    "filter": "id in 15 and chromosome eq '21' and position lt 49000000 and position gt 48097610"
  }
  resp = client.get(recomb_result_url,query_string=params)
  assert resp.status_code == 200

def test_null_chrom(client):
  recomb_result_url = "/v1/annotation/recomb/results/"

  params = {
    "filter": "id in 15 and chromosome eq 'null' and position lt 49000000 and position gt 48097610"
  }
  resp = client.get(recomb_result_url,query_string=params)
  assert resp.status_code == 400

def test_undefined_chrom(client):
  recomb_result_url = "/v1/annotation/recomb/results/"

  params = {
    "filter": "id in 15 and chromosome eq 'undefined' and position lt 49000000 and position gt 48097610"
  }
  resp = client.get(recomb_result_url,query_string=params)
  assert resp.status_code == 400

def test_null_pos(client):
  recomb_result_url = "/v1/annotation/recomb/results/"

  params = {
    "filter": "id in 15 and chromosome eq '21' and position lt null and position gt null"
  }
  resp = client.get(recomb_result_url,query_string=params)
  assert resp.status_code == 400
