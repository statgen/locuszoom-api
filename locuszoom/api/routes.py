#!/usr/bin/env python
from io import StringIO as IO
from collections import OrderedDict
from sqlalchemy import text
from flask import g, jsonify, request, Blueprint, current_app
from locuszoom.api import sentry
from locuszoom.api.jsonutil import JSONFloat
from locuszoom.api.uriparsing import SQLCompiler, LDAPITranslator, FilterParser
from locuszoom.api.models.gene import Gene, Transcript, Exon
from locuszoom.api.cache import RedisIntervalCache
from locuszoom.api.search_tokenizer import SearchTokenizer
from locuszoom.api.errors import FlaskException
from six import iteritems
from subprocess import check_output
from copy import deepcopy
import psycopg2
import redis
import requests
import traceback
import gzip
import time
import math
import re

START_TIME = time.time()

bp = Blueprint("routes", __name__, url_prefix="/v{}".format(current_app.config["API_VERSION"]))

@bp.before_request
def invalid_request_check():
  illegal_words = ["null", "undefined", "nan", "none", "\n", "\\n", ";", "="]

  filter_str = request.args.get("filter")
  if filter_str is not None:
    filter_str = filter_str.lower()
    for w in illegal_words:
      if w in filter_str:
        raise FlaskException(f"Invalid string {w} found in filter string", 400)

def std_response(db_table, db_cols, field_to_cols=None, return_json=True, return_format=None, limit=None):
  """
  Standard API response for simple cases of executing a filter against a single
  database table.

  The process is:
    * Get request arguments
    * Parse filter statement
    * Check that fields and ops requested exactly match known ones (to avoid SQL injection)
    * Create SQL query from filter statement + fields
    * Execute SQL query
    * Format data into either key --> array or array -> key:value
    * Return data

  This should be executed during a request, as it retrieves parameters directly from the request.

  Args:
    db_table: database table to query against
    db_cols: possible database columns (used to sanitize user input)
    field_to_cols: if any fields in the filter string need to be translated
      to database columns
    return_json: should we return the jsonified response (True), or just the dictionary (False)
    return_format: specify return format, can be:
      "objects" - returns an array of dictionaries, each one representing an "object"
      "table" - returns a dictionary of arrays, where key is column name

      This parameter overrides the "format" query parameter, if specified. Leave as None to use the
      format parameter in the request.

  Returns:
    Flask response w/ JSON payload containing the results of the query

    OR

    The data directly, as either
      * dictionary of key --> array (rows)
      * array of dictionaries
  """

  # Object that converts filter strings into safe SQL statements
  sql_compiler = SQLCompiler()

  # GET request parameters
  filter_str = request.args.get("filter")
  fields_str = request.args.get("fields")
  sort_str = request.args.get("sort")
  format_str = request.args.get("format")

  if fields_str is not None:
    # User's requested fields
    fields = [x.strip() for x in fields_str.split(",")]

    # Translate to database columns
    if field_to_cols is not None:
      fields = [field_to_cols.get(x,x) for x in fields]

    # To avoid injection, only accept fields that we know about
    fields = [x for x in fields if x in db_cols]
  else:
    fields = db_cols

  if sort_str is not None:
    # User's requested fields
    sort_fields = [x.strip() for x in sort_str.split(",")]

    # Translate to database columns
    if field_to_cols is not None:
      sort_fields = [field_to_cols.get(x,x) for x in sort_fields]

    # To avoid injection, only accept fields that we know about
    sort_fields = [x for x in sort_fields if x in db_cols]
  else:
    sort_fields = None

  sql, params = sql_compiler.to_sql(filter_str, db_table, db_cols, fields, sort_fields, field_to_cols, limit)

  # text() is sqlalchemy helper object when specifying SQL as plain text string
  # allows for bind parameters to be used
  cur = g.db.execute(text(sql),params)

  if return_format == "table" or (return_format is None and (format_str is None or format_str == "")):
    style = "table"
  elif return_format == "objects" or format_str == "objects":
    style = "objects"

  data = reshape_data(cur,fields,field_to_cols,style)

  if return_json:
    return jsonify({
      "data": data,
      "lastPage": None
    })
  else:
    return data

def reshape_data(rows,fields,field_to_cols=None,style="table"):
  # We may need to translate db columns --> field names.
  if field_to_cols is not None:
    cols_to_field = {v: k for k, v in field_to_cols.items()}
  else:
    cols_to_field = {v: v for v in fields}

  if style == "objects":
    data = rows_to_objects(rows,fields,cols_to_field)
  else: #assume style = "table"
    data = rows_to_arrays(rows,fields,cols_to_field)

  return data

def stringify_float(f):
  if f is None:
    return f

  if math.isinf(f):
    if f < 0:
      return "-Infinity"
    else:
      return "Infinity"

  return f

def get_float_columns(proxy):
  # 700 and 701 are the OIDs for real and double precision from postgres
  if hasattr(proxy, "cursor"):
    return [x.name for x in proxy.cursor.description if x.type_code in (700, 701)]
  elif hasattr(proxy, "description"):
    return [x.name for x in proxy.description if x.type_code in (700, 701)]
  elif isinstance(proxy, list):
    fcols = []
    for col, v in proxy[0].items():
      if isinstance(v, float):
        fcols.append(col)

    return fcols
  else:
    raise ValueError("Unexpected data type for container of database rows")

def rows_to_arrays(cur,fields,cols_to_field):
  data = OrderedDict()

  # Figure out which columns contain floating point data
  float_cols = get_float_columns(cur)

  for i, row in enumerate(cur):
    for col in fields:
      # Some of the database column names don't match field names.
      field = cols_to_field.get(col,col)
      val = row[col]
      if isinstance(val,dict):
        for k, v in val.items():
          if k not in data:
            data[k] = [None] * i

          if col in float_cols:
            data[k].append(stringify_float(v))
          else:
            data[k].append(v)
      else:
        v = row[col]
        if col in float_cols:
          v = stringify_float(v)

        data.setdefault(field,[]).append(v)

  if not data:
    # No data was found so fill with empty arrays
    db_cols = list(cur.keys())
    for col in db_cols:
      data[cols_to_field.get(col,col)] = []

  return data

def rows_to_objects(cur,fields,cols_to_field):
  data = []

  # Figure out which columns contain floating point data
  float_cols = get_float_columns(cur)

  for row in cur:
    rowdict = dict(row)
    finaldict = dict()

    # User may have requested only certain fields
    for col in fields:
      # Translate from database column to field name
      field = cols_to_field.get(col,col)
      finaldict[field] = rowdict[col]

    # Floats need special care to fix bad JSON encoding for infinity and other values
    for col in float_cols:
      if finaldict.get(col) is not None:
        finaldict[col] = stringify_float(finaldict[col])

    data.append(finaldict)

  return data

@bp.route("/status",methods = ["GET"])
def status():
  info = dict()

  # Current branch
  info["branch"] = check_output("git symbolic-ref --short -q HEAD",shell=True,universal_newlines=True).strip()

  # Current commit
  info["githash"] = check_output("git rev-parse HEAD",shell=True,universal_newlines=True).strip()

  # Uptime
  minutes, seconds = divmod(time.time() - START_TIME,60)
  hours, minutes = divmod(minutes,60)
  days, hours = divmod(hours,24)
  days, hours, minutes, seconds = list(map(int,(days,hours,minutes,round(seconds))))
  info["uptime"] = "{}d:{}h:{}m:{}s".format(days,hours,minutes,seconds)

  return jsonify(info)

@bp.route(
  "/annotation/recomb/",
  methods = ["GET"]
)
def recomb():
  # Database columns and table
  db_table = "rest.recomb"
  db_cols = ["id","name","build","version"]

  return std_response(db_table,db_cols)

@bp.route(
  "/annotation/recomb/results/",
  methods = ["GET"]
)
def recomb_results():
  # Database columns and table
  db_table = "rest.recomb_results"
  db_cols = ["id","chromosome","position","recomb_rate","pos_cm"]

  filter_str = request.args.get("filter")
  fp = FilterParser()
  matches = fp.parse(filter_str)
  lrm = fp.left_middle_right(matches)

  sql_complier = SQLCompiler()
  def fetch(terms,limit=None):
    sql, params = sql_complier.to_sql_parsed(terms,db_table,db_cols,limit=limit)
    rows = g.db.execute(text(sql),params).fetchall()
    return rows

  def interp(at,left,right):
    if left is None or right is None:
        return None
    left_at = left["position"]
    right_at = right["position"]
    left_r = left["recomb_rate"]
    right_r = right["recomb_rate"]
    result = dict(left)
    result["recom_rate"] = left_r + (at-left_at)/(right_at-left_at) * (right_r-left_r)
    result["position"] = at
    return result

  left = fetch(lrm["left"], 1)
  right =  fetch(lrm["right"], 1)
  middle = fetch(lrm["middle"])

  if len(left) < 1:
    left = [{"id": "chrleft", "position": lrm["range"]["left"],
        "chromosome": lrm["range"]["chrom"], "recomb_rate": 0, "pos_cm": 0}]
  if len(right) < 1:
    right = [{"id": "chrright", "position": lrm["range"]["right"],
        "chromosome": lrm["range"]["chrom"], "recomb_rate": 0, "pos_cm": 0}]

  if len(middle) > 0:
    left_end = interp(lrm["range"]["left"],left[0],middle[0])
    right_end = interp(lrm["range"]["right"],middle[-1],right[0])
  else:
    left_end = interp(lrm["range"]["left"],left[0],right[0])
    right_end = interp(lrm["range"]["right"],left[0],right[0])

  data = reshape_data([left_end] + middle + [right_end],db_cols)
  return jsonify({
    "data": data,
    "lastPage": None
  })

@bp.route(
  "/annotation/intervals/",
  methods = ["GET"]
)
def intervals():
  db_table = "rest.interval"
  db_cols = "id study build version type assay tissue protein histone cell_line pmid description url".split()

  return std_response(db_table,db_cols)

@bp.route(
  "/annotation/intervals/results/",
  methods = ["GET"]
)
def interval_results():
  db_table = "rest.interval_results"
  db_cols = "id public_id chrom start end strand annotation".split()

  field_to_col = dict(
    chromosome = "chrom"
  )

  return std_response(db_table,db_cols,field_to_col)

@bp.route(
  "/annotation/snps/",
  methods = ["GET"]
)
def snps():
  db_table = "rest.dbsnp_master"
  db_cols = "id genome_build dbsnp_build taxid organism".split()

  return std_response(db_table,db_cols)

@bp.route(
  "/annotation/snps/results/",
  methods = ["GET"]
)
def snps_results():
  db_table = "rest.dbsnp_snps"
  db_cols = "id rsid chrom pos ref alt".split()

  field_to_col = dict(
    chromosome = "chrom"
  )

  return std_response(db_table,db_cols,field_to_col)

@bp.route(
  "/annotation/gwascatalog/",
  methods = ["GET"]
)
def gwascat():
  db_table = "rest.gwascat_master"
  db_cols = "id name genome_build date_inserted catalog_version".split()

  return std_response(db_table,db_cols)

@bp.route(
  "/annotation/gwascatalog/results/",
  methods = ["GET"]
)
def gwascat_results():
  db_table = "rest.gwascat_data"
  db_cols = "id variant rsid chrom pos ref alt trait trait_group risk_allele risk_frq log_pvalue or_beta genes pmid pubdate first_author study".split()

  json = std_response(db_table,db_cols,return_json=False)

  if 'decompose' in request.args:
    new_json = []
    for entry in json:
      if len(entry["alt"]) == 1:
        new_json.append(entry)
      else:
        for alt in entry["alt"].split(","):
          alt_entry = deepcopy(entry)
          alt_entry["alt"] = alt
          alt_entry["variant"] = "{}:{}_{}/{}".format(entry["chrom"], entry["pos"], entry["ref"], alt)
          new_json.append(alt_entry)

    json = new_json

  variant_format = request.args.get("variant_format")
  if variant_format == "colons":
    for entry in json:
      entry["variant"] = re.sub("[:_/]",":",entry["variant"])

  return jsonify({
    "data": json,
    "lastPage": None
  })

@bp.route(
  "/statistic/single/",
  methods = ["GET"]
)
@bp.route(
  # Keep backwards compat
  "/single/",
  methods = ["GET"]
)
def single():
  db_table = "rest.assoc_master"
  db_cols = "id study trait tech build imputed analysis pmid pubdate first_author last_author".split()

  # For some reason, this database table has columns that don't match the field names in the filter string.
  field_to_col = dict(
    date = "pubdate"
  )

  return std_response(db_table,db_cols,field_to_col)

@bp.route(
  "/statistic/single/results/",
  methods = ["GET"]
)
@bp.route(
  # Keep backwards compat
  "/single/results/",
  methods = ["GET"]
)
def single_results():
  db_table = "rest.assoc_results"
  db_cols = "id variant_name chrom pos ref_allele ref_freq log_pvalue beta se score_stat".split()

  field_to_col = dict(
    analysis = "id",
    variant = "variant_name",
    chromosome = "chrom",
    position = "pos",
    score_test_stat = "score_stat",
    ref_allele_freq = "ref_freq"
  )

  limit = request.args.get("limit")
  try:
    if limit is not None:
      limit = int(limit)
  except:
    raise FlaskException("Invalid limit parameter, must be integer",400)

  return std_response(db_table,db_cols,field_to_col,limit=limit)

@bp.route(
  "/statistic/phewas/",
  methods = ["GET"]
)
def phewas():
  builds = request.args.getlist("build")
  if len(builds) == 0:
    raise FlaskException("Must provide build parameter",400)

  filter_str = request.args.get("filter")
  if filter_str is None:
    raise FlaskException("No filter string specified",400)

  fparser = FilterParser()
  stmts = fparser.statements(filter_str)
  variant = getattr(stmts.get("variant"),"value",None)
  if variant is None:
    raise FlaskException(400,"Must provide a filter string with field 'variant' specified")

  db_cols = ["id","description","study","trait","trait_label","trait_group","tech","build","pmid",
             "variant","chromosome","position","ref_allele",
             "ref_allele_freq","log_pvalue","beta","se","score_test_stat"]

  sql = """
    SELECT
      sa.id,sa.study,sa.trait,traits.label as trait_label,traits.grouping as trait_group,sa.tech,sa.build,sa.analysis as description,sa.pmid,
      sr.variant_name as variant,sr.chrom as chromosome,sr.pos as position,sr.ref_allele,sr.ref_freq as ref_allele_freq,
      sr.log_pvalue,sr.beta,sr.se,sr.score_stat as score_test_stat
    FROM rest.assoc_master sa
      JOIN rest.assoc_results sr ON sa.id = sr.id
      LEFT JOIN rest.traits ON sa.trait = traits.trait
    WHERE variant_name = :vname
      AND sa.build = ANY(:builds)
      AND traits.grouping IS NOT NULL
      AND traits.label IS NOT NULL
    ORDER BY log_pvalue DESC;
  """

  return_fmt = request.args.get("format")
  if return_fmt is None or return_fmt == "":
    return_fmt = "table"

  if return_fmt not in ("table","objects"):
    raise FlaskException(400,"format must be either 'table' or 'objects'")

  cur = g.db.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
  cur.callproc("rest.phewas_query",[variant,builds])
  data = reshape_data(cur,db_cols,None,return_fmt)
  return jsonify({
    "meta": {
      "build": builds
    },
    "data": data,
    "lastPage": None
  })

@bp.route(
  "/statistic/pair/LD/results/",
  methods = ["GET"]
)
@bp.route(
  # Keep backwards compat
  "/pair/LD/results/",
  methods = ["GET"]
)
def ld_results():
  # GET request parameters
  filter_str = request.args.get("filter")
  #fields_str = request.args.get("fields")
  #sort_str = request.args.get("sort")
  #format_str = request.args.get("format")

  if filter_str is None:
    raise FlaskException("No filter string specified",400)

  # Figure out the LD API URL to send the request through
  #base_url = "http://localhost:8888/api_ld/ld?"
  base_url = "http://portaldev.sph.umich.edu/api_ld/ld?"
  trans = LDAPITranslator()
  param_str, param_dict = trans.to_refsnp_url(filter_str)
  final_url = base_url + param_str

  # Cache
  ld_cache = RedisIntervalCache(g.redis_client)

  # Cache key for this particular request.
  # Note that in Daniel's API, for now, "reference" is implicitly
  # attached to build, reference panel, and population all at the same time.
  # In the future, it will hopefully expand to accepting paramters for all 3, and
  # then we can include this in the cache key.
  if "variant1" not in param_dict:
    raise FlaskException("Must provide variant1 in filter",400)

  if "reference" not in param_dict:
    raise FlaskException("Must provide reference in filter",400)

  refvariant = param_dict["variant1"]["eq"][0]
  reference = param_dict["reference"]["eq"][0]
  refpos = int(refvariant.split("_")[0].split(":")[1])

  cache_key = "{reference}__{refvariant}".format(
    reference = reference,
    refvariant = refvariant
  )

  try:
    start = int(param_dict["position2"]["ge"][0])
    end = int(param_dict["position2"]["le"][0])
  except:
    raise FlaskException("position2 compared to non-integer",400)

  chromosome = param_dict["chromosome2"]["eq"][0]
  rlength = abs(end - start)

  # Is the region larger than we're willing to calculate?
  max_ld_size = current_app.config["LD_MAX_SIZE"]
  if math.fabs(end - start) > max_ld_size:
    raise FlaskException("Requested LD window is too large, exceeded maximum of {}".format(max_ld_size),413)

  outer = {
    "data": None,
    "lastPage": None
  }

  data = {
    "chromosome2": [],
    "position2": [],
    "rsquare": [],
    "variant2": []
  }

  outer["data"] = data

  # Do we need to compute, or is the cache sufficient?
  cache_data = None
  try:
    cache_data = ld_cache.retrieve(cache_key,start,end)
  except redis.ConnectionError:
    print("Warning: cache retrieval failed (redis was unable to connect)")
  except:
    print("Error: redis connected, but retrieving data failed")
    traceback.print_exc()

  if cache_data is None:
    # Need to compute. Either the range given is larger than we've previously computed,
    # or redis is down.
    print("Cache miss for {reference}__{refvariant} in {start}-{end} ({rlength:,.2f}kb), recalculating".format(
      reference=reference,
      refvariant=refvariant,
      start=start,
      end=end,
      rlength=rlength/1000
    ))

    # Fire off the request to the LD server.
    try:
      resp = requests.get(final_url)
    except Exception as e:
      raise FlaskException("Failed retrieving data from LD server, error was {}".format(e.message),500)

    # Did it come back OK?
    if not resp.ok:
      raise FlaskException("Failed retrieving data from LD server, error was {}".format(resp.reason),500)

    # Get JSON
    ld_json = resp.json()

    # Store in format needed for API response
    for obj in ld_json["pairs"]:
      data["chromosome2"].append(ld_json["chromosome"])
      data["position2"].append(obj["position2"])
      data["rsquare"].append(JSONFloat(obj["rsquare"]))
      data["variant2"].append(obj["name2"])

    # Store data to cache
    keep = ("name2","rsquare")
    for_cache = dict(zip(
      (x["position2"] for x in ld_json["pairs"]),
      (dict((x,d[x]) for x in keep) for d in ld_json["pairs"])
    ))

    if len(for_cache) > 0:
      # If we actually received LD data for this variant, store it in the cache.
      try:
        ld_cache.store(cache_key,start,end,for_cache)
      except redis.ConnectionError:
        print("Warning: cache storage failed (redis was unable to connect)")
      except:
        print("Error: storing data in cache failed, traceback was: ")
        traceback.print_exc()

  else:
    print("Cache *match* for {reference}__{refvariant} in {start}-{end} ({rlength:,.2f}kb), using cached data".format(
      reference=reference,
      refvariant=refvariant,
      start=start,
      end=end,
      rlength=rlength/1000
    ))

    # We can just use the cache's data directly.
    for position, ld_pair in iteritems(cache_data):
      data["chromosome2"].append(chromosome)
      data["position2"].append(position)
      data["rsquare"].append(JSONFloat(ld_pair["rsquare"]))
      data["variant2"].append(ld_pair["name2"])

  final_resp = jsonify(outer)

  return final_resp

@bp.route(
  "/annotation/genes/sources/",
  methods = ["GET"]
)
def gene_sources():
  db_table = "rest.gene_master"
  db_cols = "id source version genome_build taxid organism".split()
  return std_response(db_table,db_cols)

def fetch_recommended_id(build, table):
  """
  Return the recommended dataset for a given database table and genome build.

  This is typically the dataset corresponding to:
    1) The "best" source (for example, gencode is our preferred gene source)
    2) The latest inserted table for that source

  :param build: Genome build, e.g. 'GRCh37'
  :param table: Database table. Possible options are 'gene_master', 'gwascat_master', 'recomb'
  :return: ID for the recommended dataset
  """
  sql = f"SELECT * FROM rest.recommended WHERE db_table = '{table}' AND genome_build='{build}'"
  cur = g.db.execute(text(sql))
  res = cur.fetchone()
  return res[0] if res is not None else None

@bp.route(
  "/annotation/genes/",
  methods = ["GET"]
)
def genes():
  db_table = "rest.gene_data"
  db_cols = "id feature_type gene_id gene_name chrom start end strand transcript_id exon_id annotation".split()

  field_to_col = {
    "source": "id"
  }

  orig_filter = request.args.get("filter")
  if orig_filter is None:
    raise FlaskException("Filter is a required parameter for this endpoint")

  sql_compiler = SQLCompiler()

  cols = "id gene_id gene_name chrom start end strand annotation".split()
  sql_stmt, sql_params = sql_compiler.to_sql(orig_filter,db_table,db_cols,cols,None,field_to_col)
  sql_stmt += " AND feature_type = 'gene'"

  cur = g.db.execute(text(sql_stmt),sql_params)
  dgenes = {}
  genes_arr = []
  for row in cur:
    gene_data = dict(zip(cols,row))
    annotation = gene_data.pop("annotation")
    gene_data["gene_type"] = annotation["gene_type"]
    gene = Gene(**gene_data)
    dgenes[gene_data["gene_id"]] = gene
    genes_arr.append(gene)

  # Now retrieve transcripts/exons
  # Only retrieve if there were genes found in the region
  skip_transcripts = request.args.get("transcripts","").lower() in ("f","false","no")
  if not skip_transcripts and len(genes_arr) > 0:
    cols = "id feature_type gene_id chrom start end strand transcript_id exon_id".split()
    trans_keys = "transcript_id chrom start end strand".split()
    exon_keys = "exon_id chrom start end strand".split()
    dtranscripts = {}

    fp = FilterParser()
    sources = fp.statements(orig_filter)["source"].value

    sql_stmt = (
      "SELECT {} from {} "
      "WHERE id in :p1 AND gene_id IN :p2 AND feature_type IN ('transcript','exon') "
      "ORDER BY CASE feature_type WHEN 'transcript' THEN 1 WHEN 'exon' THEN 2 ELSE 3 END "
    ).format(",".join(map(sql_compiler.quote_keywords,cols)),db_table)

    sql_params = {
      "p1": tuple(sources),
      "p2": tuple(dgenes.keys()),
    }

    cur = g.db.execute(text(sql_stmt),sql_params)
    for row in cur:
      rowd = dict(zip(cols,row))

      if rowd["feature_type"] == "transcript":
        tx_id = row["transcript_id"]
        gene_id = row["gene_id"]
        chrom = row["chrom"]

        transcript = dtranscripts.get(tx_id,None)
        if transcript is None:
          transcript_data = {k: rowd[k] for k in trans_keys}
          transcript = Transcript(**transcript_data)
          dtranscripts[tx_id] = transcript
          dgenes[gene_id].add_transcript(transcript)

      elif rowd["feature_type"] == "exon":
        gene_id = row["gene_id"]
        tx_id = row["transcript_id"]
        exon_id = row["exon_id"]
        exon_data = {k: rowd[k] for k in exon_keys}
        exon = Exon(**exon_data)

        gene = dgenes.get(gene_id)
        if gene is not None:
          gene.add_exon(exon)

        transcript = dtranscripts.get(tx_id)
        if transcript is not None:
          transcript.add_exon(exon)

  json_genes = [gene.to_dict() for gene in genes_arr]

  outer = {
    "data": json_genes,
    "lastPage": None
  }

  return jsonify(outer)

@bp.route(
  "/annotation/omnisearch/",
  methods = ["GET"]
)
def omnisearch():
    """
    This function is meant to take a generic search term and return
    a genomic position

    We will support the following search types
    * chr:position
    * chr:start-stop
    * chr:position+offset (-> chr:position-offset - chr:position+offset)
    * rs00001
    * rs00001+offset
    * gene symbol names
    * transcript names

    Positions and offsets may have commas and use K and M suffixes
    """

    def gene_lookup_base(x, filter_str, build):
        build_id = g.build_id.get(build, {}).get("genes", None)
        if build_id is None:
            x["error"] = "Genes not available for build"
            return x

        filter_str = " and ".join([f for f in [filter_str, "source_id eq {}".format(build_id)] if len(f)>0])
        filter_str += " and feature_type eq 'gene'"

        sql_complier = SQLCompiler()
        db_table = "rest.gene_data"

        ok_fields = "id gene_id gene_name chrom start end strand feature_type".split()
        db_cols = "id chrom gene_name gene_id start end".split()

        sort_fields = ["chrom","start"]
        fields_to_col = {
          "source_id": "id",
          "chromosome": "chrom",
          "interval_start": "start",
          "interval_end": "end"
        }

        sql, params = sql_complier.to_sql(filter_str, db_table, ok_fields, db_cols, sort_fields, fields_to_col, None)
        cur = g.db.execute(text(sql), params)

        results = cur.fetchmany(2)
        if len(results)==1:
            row = results[0]
            x["chrom"] = row["chrom"]
            x["start"] = row["start"] - x.get("offset", 0)
            x["end"] = row["end"] + x.get("offset", 0)
            x["gene_name"] = row["gene_name"]
            x["gene_id"] = row["gene_id"]
            del x["q"]
            del x["offset"]
            return x
        elif len(results)==0:
            x["error"] = "Gene not found"
            return x
        elif len(results)>1:
            x["error"] = "Gene name not unique"
            return x

    def gene_name_lookup(x, build):
        term = x.get("q",None)
        if term is None:
            return x
        sql_complier = SQLCompiler()
        filter_str = "gene_name eq '{}'".format(term.upper())
        return gene_lookup_base(x, filter_str, build)

    def gene_id_lookup(x, build):
        term = x.get("q",None)
        if term is None:
            return x
        sql_complier = SQLCompiler()
        filter_str = "gene_id like '{}%'".format(term.upper())
        return gene_lookup_base(x, filter_str, build)

    def rs_lookup(x, build):
        term = x.get("q",None)
        if term is None:
            return x
        build_id = g.build_id.get(build, {}).get("db_snp", None)
        if build_id is None:
            x["error"] = "SNP positions not available for build"
            return x
        sql_complier = SQLCompiler()
        filter_str = "id eq {} and rsid eq '{}'".format(build_id, term.lower())
        fields = ["chrom", "pos"]
        db_table = "rest.dbsnp_snps"
        sort_fields = ["chrom","pos"]
        db_cols = "id rsid chrom pos ref alt".split()
        sql, params = sql_complier.to_sql(filter_str, db_table, db_cols, fields, sort_fields, None)
        cur = g.db.execute(text(sql), params)
        results = cur.fetchmany(2)
        if len(results)==1:
            row = results[0]
            x["chrom"] = row["chrom"]
            x["start"] = row["pos"] - x.get("offset", 0)
            x["end"] = row["pos"] + x.get("offset", 0)
            del x["q"]
            del x["offset"]
            return x
        elif len(results)==0:
            x["error"] = "SNP not found"
            return x
        elif len(results)>1:
            x["error"] = "SNP not unique"
            return x

    term_arg = request.args.get("q")
    build_arg = request.args.get("build")

    if term_arg is None or build_arg is None:
        resp = jsonify({"error": "Missing 1 or more required parameters: q, build"})
        resp.status_code = 422
        return resp

    if build_arg.lower() not in g.build_id:
        resp = jsonify({"error": "Unrecognized build (" + build_arg + "), known: " + ", ".join(g.build_id.keys())})
        resp.status_code = 422
        return resp
    build = build_arg.lower()

    st = SearchTokenizer(term_arg)
    results = []
    for x in st.get_terms():
        if "type" not in x:
            results.append(x)
        elif x["type"] == "region":
            results.append(x)
        elif x["type"] == "rs":
            results.append(rs_lookup(x, build))
        elif x["type"] == "egene":
            results.append(gene_id_lookup(x, build))
        elif x["type"] == "other":
            results.append(gene_name_lookup(x, build))
        else:
            x["error"] = "Cannot look up position"
            results.append(x)

    return jsonify({"build": build, "data": results})
