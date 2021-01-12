def test_annotation_gwascatalog(client):
  # Check metadata endpoint
  resp = client.get("/v1/annotation/gwascatalog/")
  assert resp.status_code == 200

  data = resp.json
  for k in "id name genome_build date_inserted catalog_version".split():
    assert k in data["data"]
    assert len(data["data"][k]) > 1

  # Check results endpoint
  test_id = data["data"]["id"][0]
  params = {
    "filter": "id in {} and rsid eq 'rs7903146'".format(test_id),
    "limit": 1,
    "sort": "pos"
  }
  results = client.get("/v1/annotation/gwascatalog/results/",query_string=params)

  assert results.status_code == 200

  result_data = results.json
  assert "data" in result_data
  assert len(result_data["data"]) > 0

  for k in "id variant rsid chrom pos ref alt trait trait_group risk_allele risk_frq log_pvalue or_beta genes pmid pubdate first_author study".split():
    assert k in result_data["data"]

def test_annotation_gwascatalog_colons(client):
  # Check metadata endpoint
  resp = client.get("/v1/annotation/gwascatalog/")
  assert resp.status_code == 200

  # Check results endpoint
  data = resp.json
  test_id = data["data"]["id"][0]
  params = {
    "filter": "id in {} and rsid eq 'rs7903146'".format(test_id),
    "limit": 1,
    "sort": "pos",
    "format": "objects",
    "variant_format": "colons"
  }
  results = client.get("/v1/annotation/gwascatalog/results/",query_string=params)

  assert results.status_code == 200

  result_data = results.json
  assert "data" in result_data
  assert len(result_data["data"]) > 0

  for entry in result_data["data"]:
    for k in "id variant rsid chrom pos ref alt trait trait_group risk_allele risk_frq log_pvalue or_beta genes pmid pubdate first_author study".split():
      assert k in entry

    assert '_' not in entry["variant"]
    assert '/' not in entry["variant"]