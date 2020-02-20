import requests, os
from flask import url_for
from six import string_types

def test_gene(client):
  params = {
    "filter": "source in 2 and chrom eq '16' and start le 57022881 and end ge 56985060"
  }
  resp = client.get("/v1/annotation/genes/",query_string=params)

  assert resp.status_code == 200
  assert len(resp.json["data"]) > 0

  # Check format of gene
  for gene in resp.json["data"]:
    for key in ("chrom","end","exons","gene_id","gene_name","start","strand","transcripts"):
      assert key in gene

    assert isinstance(gene["chrom"],string_types)
    assert isinstance(gene["gene_id"],string_types)
    assert isinstance(gene["gene_name"],string_types)
    assert gene["strand"] in ("+","-")
    assert isinstance(gene["end"],int)
    assert isinstance(gene["start"],int)

    assert len(gene["exons"]) > 0

    for exon in gene["exons"]:
      for key in ("chrom","end","exon_id","start","strand"):
        assert key in exon

      assert isinstance(exon["exon_id"],string_types)
      assert isinstance(exon["chrom"],string_types)
      assert isinstance(exon["end"],int)
      assert isinstance(exon["start"],int)
      assert exon["strand"] in ("+","-")

    assert len(gene["transcripts"]) > 0

    for tx in gene["transcripts"]:
      for key in ("chrom","end","exons","start","strand","transcript_id"):
        assert key in tx

      assert isinstance(tx["transcript_id"],string_types)
      assert isinstance(tx["chrom"],string_types)
      assert isinstance(tx["end"],int)
      assert isinstance(tx["start"],int)
      assert tx["strand"] in ("+","-")
      assert len(tx["exons"]) > 0

def test_gene_chrom_null(client):
  params = {
    "filter": "source in 2 and chrom eq 'null' and start le 57022881 and end ge 56985060"
  }
  resp = client.get("/v1/annotation/genes/",query_string=params)

  assert resp.status_code == 400

def test_gene_chrom_undefined(client):
  params = {
    "filter": "source in 2 and chrom eq 'undefined' and start le 57022881 and end ge 56985060"
  }
  resp = client.get("/v1/annotation/genes/",query_string=params)

  assert resp.status_code == 400

def test_no_genes(client):
  """
  Test region that should contain no genes
  """

  params = {
    "filter": "source in 2 and chrom eq '16' and start le 54265502 and end ge 54164840"
  }
  resp = client.get("/v1/annotation/genes/",query_string=params)
  assert resp.status_code == 200

  assert len(resp.json["data"]) == 0

def test_wwox(client):
  """
  This region perfectly excludes all of the exons of 1 transcript of WWOX
  Previously this caused an error because locuszoom expects all transcripts returned
  to have at least one exon

  16:78189937-79189937
  """

  params = {
    "filter": "source in 2 and chrom eq '16' and start le 79189937 and end ge 78189937"
  }
  resp = client.get("/v1/annotation/genes/",query_string=params)
  assert resp.status_code == 200

  assert len(resp.json["data"]) > 0

  for gene in resp.json["data"]:
    for tx in gene["transcripts"]:
      for key in ("chrom","end","exons","start","strand","transcript_id"):
        assert key in tx

      assert isinstance(tx["transcript_id"],string_types)
      assert isinstance(tx["chrom"],string_types)
      assert isinstance(tx["end"],int)
      assert isinstance(tx["start"],int)
      assert tx["strand"] in ("+","-")
      assert len(tx["exons"]) > 0

def test_skip_transcripts(client):
  """
  Make sure gene query honors transcripts=F
  """

  params = {
    "filter": "source in 2 and chrom eq '16' and start le 57022881 and end ge 56985060",
    "transcripts": "F"
  }
  resp = client.get("/v1/annotation/genes/",query_string=params)
  assert resp.status_code == 200

  assert len(resp.json["data"]) > 0
  for gene in resp.json["data"]:
    assert "transcripts" not in gene
    assert "exons" not in gene
