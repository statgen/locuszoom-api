from six import string_types

def test_omni(client):
  params = {
    "q": "CSF3",
    "build": "GRCh38"
  }
  resp = client.get("/v1/annotation/omnisearch/",query_string=params)
  assert resp.status_code == 200

  js = resp.json

  assert len(js["data"]) > 0

  # Check format
  for gene in js["data"]:
    for key in ("chrom","end","gene_id","gene_name","start","term","type"):
      assert key in gene

    assert isinstance(gene["chrom"],string_types)
    assert isinstance(gene["gene_id"],string_types)
    assert isinstance(gene["gene_name"],string_types)
    assert isinstance(gene["end"],int)
    assert isinstance(gene["start"],int)

  assert isinstance(js["build"],string_types)
  assert js["build"].lower().startswith("grch")
