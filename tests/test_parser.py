def test_invalid_op(client):
  params = {
    "filter": "trait is 'BMI'"
  }
  resp = client.get("/v1/statistic/single/",query_string=params)
  assert resp.status_code == 400
  data = resp.json
  assert "Incorrect syntax" in data["message"]

