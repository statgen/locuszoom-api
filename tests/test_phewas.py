def test_phewas(client):
  params = {
    "filter": "variant eq '10:114758349_C/T'",
    "build": ["GRCh37","GRCh38"]
  }
  resp = client.get("/v1/statistic/phewas/",query_string=params)
  assert resp.status_code == 200

  data = resp.json
  fields = "description build chromosome id log_pvalue pmid position ref_allele ref_allele_freq score_test_stat " \
           "study tech trait trait_group trait_label variant".split()

  for k in fields:
    assert k in data["data"]
    assert len(data["data"][k]) > 1

  # PheWAS plots will not function without a trait label or group
  # Datasets without a trait group or label should not be returned by the API endpoint
  assert all(x is not None for x in data["data"]["trait_group"])
  assert all(x is not None for x in data["data"]["trait_label"])

def test_infinity_objects(client):
  """
  Test that Infinity in the database gets translated into the string "Infinity" in the response. A plain Infinity is apparently invalid JSON.
  """

  params = {
    "filter": "variant eq '16:65928770_C/T'",
    "build": ["GRCh37","GRCh38"],
    "format": "objects"
  }
  resp = client.get("/v1/statistic/phewas/",query_string=params)
  assert resp.status_code == 200

  data = resp.json
  assert data["data"][0]["log_pvalue"] == "Infinity"

def test_infinity_arrays(client):
  """
  Test that Infinity in the database gets translated into the string "Infinity" in the response. A plain Infinity is apparently invalid JSON.
  """

  params = {
    "filter": "variant eq '16:65928770_C/T'",
    "build": ["GRCh37","GRCh38"]
  }
  resp = client.get("/v1/statistic/phewas/",query_string=params)
  assert resp.status_code == 200

  data = resp.json
  assert data["data"]["log_pvalue"][0] == "Infinity"
