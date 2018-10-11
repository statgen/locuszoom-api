def test_annotation_snps(client):
  resp = client.get("/v1/annotation/snps/")
  assert resp.status_code == 200

  data = resp.json
  assert len(data["data"]["id"]) >= 1

  test_id = data["data"]["id"][0]
  params = {
    # Every dbSNP version under the sun should contain rs7903146
    "filter": "id eq {} and rsid eq 'rs7903146'".format(test_id)
  }
  results = client.get("/v1/annotation/snps/results/",query_string=params)

  assert results.status_code == 200
  result_data = results.json

  assert "data" in result_data
  assert len(result_data["data"]) > 0

  for k in ("alt","chromosome","id","pos","ref","rsid"):
    assert k in result_data["data"]

  # All columns should have the same length
  assert len(set(map(len,result_data["data"].values()))) == 1
