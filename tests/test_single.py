import requests, os, pytest
from locuszoom.api import create_app

@pytest.fixture
def client():
  app = create_app()
  client = app.test_client()
  return client

def test_statistic_single_experiment(client):
  resp = client.get("/v1/statistic/single/")
  assert resp.status_code == 200

  for k in "analysis build date first_author last_author id imputed pmid study tech trait".split():
    assert k in resp.json["data"]
    assert len(resp.json["data"][k]) > 1
