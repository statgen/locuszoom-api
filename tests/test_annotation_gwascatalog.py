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

def test_metadata(client):
  params = {
    "filter": "id in 2 and rsid eq 'rs7903146'",
    "limit": 1,
    "sort": "pos"
  }
  results = client.get("/v1/annotation/gwascatalog/results/",query_string=params)
  meta = results.json["meta"]
  for d in meta["datasets"]:
    assert "genome_build" in d
    assert "version" in d
    assert "name" in d
    assert "id" in d

def test_recommended_gwascat_results(client):
  # Check results endpoint
  params = {
    "filter": "rsid eq 'rs7903146'",
    "limit": 1,
    "sort": "pos",
    "build": "GRCh37"
  }
  results = client.get("/v1/annotation/gwascatalog/results/",query_string=params)

  assert results.status_code == 200

  result_data = results.json
  assert "data" in result_data
  assert len(result_data["data"]) > 0

  for k in "id variant rsid chrom pos ref alt trait trait_group risk_allele risk_frq log_pvalue or_beta genes pmid pubdate first_author study".split():
    assert k in result_data["data"]

def test_annotation_gwascatalog_colons_decompose_noobj(client):
  test_id = 2
  params = {
    "filter": "id in {}".format(test_id),
    "sort": "pos",
    "decompose": 1,
    "variant_format": "colons"
  }
  results = client.get("/v1/annotation/gwascatalog/results/",query_string=params)

  assert results.status_code == 200

  result_data = results.json
  assert "data" in result_data

  data = result_data["data"]
  assert len(data) > 0

  for k in "id variant rsid chrom pos ref alt trait trait_group risk_allele risk_frq log_pvalue or_beta genes pmid pubdate first_author study".split():
    assert k in data

  for i in range(len(data["variant"])):
    variant = data["variant"][i]
    alt = data["alt"][i]

    assert len(alt) == 1
    assert "," not in variant
    assert '_' not in variant
    assert '/' not in variant

def test_build_and_id_validate(client):
  # Check results endpoint
  params = {
    "filter": "id in 1 and rsid eq 'rs7903146'",
    "limit": 1,
    "sort": "pos",
    "build": "GRCh38"
  }
  results = client.get("/v1/annotation/gwascatalog/results/",query_string=params)
  assert results.status_code == 200

  bad_params = {
    "filter": "id in 1 and rsid eq 'rs7903146'",
    "limit": 1,
    "sort": "pos",
    "build": "GRCh37"
  }
  results = client.get("/v1/annotation/gwascatalog/results/",query_string=bad_params)
  assert results.status_code == 400

def test_recommended_gwascat_results_missing_build(client):
  # Check results endpoint
  params = {
    "filter": "rsid eq 'rs7903146'",
    "limit": 1,
    "sort": "pos"
  }
  results = client.get("/v1/annotation/gwascatalog/results/",query_string=params)

  assert results.status_code == 400

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

def test_annotation_gwascatalog_metadata(client):
  params = {
    "filter": "id in 2,3 and rsid eq 'rs7903146'",
    "limit": 1,
    "sort": "pos"
  }
  results = client.get("/v1/annotation/gwascatalog/results/",query_string=params)

  assert results.status_code == 200

  result_data = results.json
  assert "data" in result_data
  assert len(result_data["data"]) > 0

  found_ids = set()
  for entry in result_data["meta"]["datasets"]:
    found_ids.add(entry["id"])

  assert 2 in found_ids
  assert 3 in found_ids

  for k in "id variant rsid chrom pos ref alt trait trait_group risk_allele risk_frq log_pvalue or_beta genes pmid pubdate first_author study".split():
    assert k in result_data["data"]

def test_annotation_gwascatalog_multiallelic(client):
  test_id = 2
  params = {
    "filter": "id in {}".format(test_id),
    "sort": "pos",
    "format": "objects",
    "decompose": 1,
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

    assert len(entry["alt"]) == 1
    assert "," not in entry["variant"]
    assert '_' not in entry["variant"]
    assert '/' not in entry["variant"]