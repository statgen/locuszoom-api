from six import string_types

def test_ld_small(client):
  params = {
    "filter": "reference eq 1 and chromosome2 eq '16' and position2 ge 56859412 and position2 le 57059412 and variant1 eq '16:56989590_C/T'"
  }
  resp = client.get("/v1/statistic/pair/LD/results/",query_string=params)
  assert resp.status_code == 200

  js = resp.json
  data = js["data"]

  assert len(js["data"]) > 0

  # Check format
  for key in ("chromosome2","position2","rsquare","variant2"):
    assert key in data

  assert isinstance(data["chromosome2"][0],string_types)
  assert isinstance(data["position2"][0],int)
  assert isinstance(data["rsquare"][0],float)
  assert isinstance(data["variant2"][0],string_types)

  def check_variant_format(v):
    split = v.split("_")

    try:
      chrom, pos = split[0].split(":")
      int(pos)
    except:
      return False

    try:
      ref, alt = split[1].split("/")
    except:
      return False

    return True

  assert all(map(check_variant_format,data["variant2"]))

  def check_rsquare(v):
    return (v >= 0) and (v <= 1)

  assert all(map(check_rsquare,data["rsquare"]))
