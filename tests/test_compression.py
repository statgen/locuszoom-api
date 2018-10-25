import requests, os, pytest
from locuszoom.api import create_app

@pytest.fixture
def client():
  app = create_app()
  client = app.test_client()
  return client

def test_compress(client):
  resp_comp = client.get("/v1/statistic/single/",headers={"Accept-Encoding": "gzip"})
  assert resp_comp.status_code == 200
  assert "gzip" in resp_comp.headers["Content-Encoding"]

  resp_nocomp = client.get("/v1/statistic/single/",headers={"Accept-Encoding": "identity"})
  assert resp_nocomp.status_code == 200
  assert "Content-Encoding" not in resp_nocomp.headers

  assert int(resp_comp.headers["Content-Length"]) < int(resp_nocomp.headers["Content-Length"])
