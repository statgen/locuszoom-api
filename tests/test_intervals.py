from six import string_types

def test_intervals(client):
  params = {
    "filter": "id in 18 and chromosome eq '16' and start le 54119169 and end ge 53519169"
  }
  resp = client.get("/v1/annotation/intervals/results/",query_string=params)
  assert resp.status_code == 200

  js = resp.json
  data = js["data"]

  assert len(data) > 0

  # Check format
  columns = ("chromosome","end","id","public_id","start","strand","state_id","state_name")
  for key in columns:
    assert key in data

  assert isinstance(data["chromosome"][0],string_types)

  def check_id(v):
    try:
      v == int(v)
      v > 0
    except:
      return False
    else:
      return True

  assert all(map(check_id,data["id"]))

  def check_state_id(v):
    try:
      v == int(v)
    except:
      return False
    else:
      return True

  assert all(map(check_state_id,data["state_id"]))

  def check_pos(v):
    try:
      v == int(v)
      v > 0
    except:
      return False
    else:
      return True

  assert all(map(check_pos,data["start"]))
  assert all(map(check_pos,data["end"]))

  # Check that all vectors are same length
  assert len(set(map(len,data.values()))) == 1
