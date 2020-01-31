def test_statistic_single_results(client):
  resp = client.get("/v1/statistic/single/")
  assert resp.status_code == 200

  data = resp.json
  assert len(data["data"]["id"]) > 1

  test_id = data["data"]["id"][0]
  params = {
    "filter": "analysis in {} and chromosome in '16' and position ge 0 and position le 200000000".format(test_id),
    "limit": 1,
    "sort": "position"
  }
  results = client.get("/v1/statistic/single/results/",query_string=params)

  assert results.status_code == 200
  result_data = results.json
  assert "data" in result_data
  assert len(result_data["data"]) > 0
  for k in ("analysis","chromosome","log_pvalue","position","ref_allele","ref_allele_freq","score_test_stat","variant"):
    assert k in result_data["data"]

def test_statistic_single_results_objects(client):
  resp = client.get("/v1/statistic/single/")
  assert resp.status_code == 200

  data = resp.json
  assert len(data["data"]["id"]) > 1

  test_id = data["data"]["id"][0]
  params = {
    "filter": "analysis in {} and chromosome in '16' and position ge 0 and position le 200000000".format(test_id),
    "limit": 1,
    "sort": "position",
    "format": "objects"
  }
  results = client.get("/v1/statistic/single/results/",query_string=params)

  assert results.status_code == 200
  result_data = results.json
  assert "data" in result_data
  assert len(result_data["data"]) > 0
  for k in ("analysis","chromosome","log_pvalue","position","ref_allele","ref_allele_freq","score_test_stat","variant"):
    assert k in result_data["data"][0]

def test_empty_region(client):
  params = {
    "filter": "analysis in 45 and chromosome in '2' and position ge 242023897 and position le 242025881"
  }

  results = client.get("/v1/statistic/single/results/",query_string=params)
  assert results.status_code == 200

  data = results.json["data"]
  for k in ("analysis","chromosome","log_pvalue","position","ref_allele","ref_allele_freq","score_test_stat","variant","beta","se"):
    assert k in data
    assert isinstance(data[k],list)
    assert len(data[k]) == 0
