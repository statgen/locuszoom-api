#!/usr/bin/env python
from cStringIO import StringIO as IO
from collections import OrderedDict
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import URL
from flask import g, jsonify, request
from portalapi import app, cache
from portalapi.uriparsing import SQLCompiler, LDAPITranslator, FilterParser
from portalapi.models.gene import Gene, Transcript, Exon
from portalapi.cache import RedisIntervalCache
from portalapi.search_tokenizer import SearchTokenizer
from pyparsing import ParseException, ParseResults
from six import iteritems
from subprocess import check_output
import requests
import psycopg2
import redis
import traceback
import gzip
import time

START_TIME = time.time()

engine = create_engine(
  URL(**app.config["DATABASE"]),
  connect_args = dict(
    application_name = app.config["DB_APP_NAME"]
  ),
  pool_size = 5,
  max_overflow = 0,
  isolation_level = "AUTOCOMMIT"
  # poolclass = NullPool
)

redis_client = redis.StrictRedis(
  host = app.config["REDIS_HOST"],
  port = app.config["REDIS_PORT"],
  db = app.config["REDIS_DB"]
)

class FlaskException(Exception):
  status_code = 400

  def __init__(self, message, status_code=None, payload=None):
    Exception.__init__(self)
    self.message = message
    if status_code is not None:
      self.status_code = status_code
    self.payload = payload

  def to_dict(self):
    rv = dict(self.payload or ())
    rv['message'] = self.message
    return rv

@app.errorhandler(FlaskException)
def handle_exception(error):
  response = jsonify(error.to_dict())
  response.status_code = error.status_code
  return response

@app.errorhandler(ParseException)
def handle_parse_error(error):
  response = jsonify({
    "message": "Incorrect syntax in filter string, error was: " + error.msg
  })

  response.status_code = 400
  return response

@app.before_request
def before_request():
  global engine

  db = getattr(g,"db",None)
  if db is None:
    db = engine.connect()
  g.db = db

  # Hard coded for now - should look up from DB
  build_id = getattr(g, "build_id", None)
  if build_id is None:
    build_id = {"grch37": {"db_snp": 9, "genes": 2},
        "grch38": {"genes": 1}}
    g.build_id = build_id

@app.teardown_appcontext
def close_db(*args):
  db = getattr(g,"db",None)
  if db is not None:
    db.close()

@app.after_request
def zipper(response):
  if not request.args.get("compress"):
    return response

  accept_encoding = request.headers.get('Accept-Encoding', '')

  if 'gzip' not in accept_encoding.lower():
    return response

  response.direct_passthrough = False

  if (response.status_code < 200 or
    response.status_code >= 300 or
    'Content-Encoding' in response.headers):
    return response

  gzip_buffer = IO()
  gzip_file = gzip.GzipFile(mode='wb',fileobj=gzip_buffer)
  gzip_file.write(response.data)
  gzip_file.close()

  response.data = gzip_buffer.getvalue()
  response.headers['Content-Encoding'] = 'gzip'
  response.headers['Vary'] = 'Accept-Encoding'
  response.headers['Content-Length'] = len(response.data)

  return response

class JSONFloat(float):
  def __repr__(self):
    return "%0.2g" % self

def std_response(db_table, db_cols, field_to_cols=None, return_json=True, return_format=None):
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
    fields = map(lambda x: x.strip(),fields_str.split(","))

    # Translate to database columns
    if field_to_cols is not None:
      fields = map(lambda x: field_to_cols.get(x,x),fields)

    # To avoid injection, only accept fields that we know about
    fields = filter(lambda x: x in db_cols,fields)
  else:
    fields = db_cols

  if sort_str is not None:
    # User's requested fields
    sort_fields = map(lambda x: x.strip(),sort_str.split(","))

    # Translate to database columns
    if field_to_cols is not None:
      sort_fields = map(lambda x: field_to_cols.get(x,x),sort_fields)

    # To avoid injection, only accept fields that we know about
    sort_fields = filter(lambda x: x in db_cols,sort_fields)
  else:
    sort_fields = None

  sql, params = sql_compiler.to_sql(filter_str, db_table, db_cols, fields, sort_fields, field_to_cols)

  # text() is sqlalchemy helper object when specifying SQL as plain text string
  # allows for bind parameters to be used
  cur = g.db.execute(text(sql),params)

  if return_format == "table" or (return_format is None and (format_str is None or format_str == "")):
    style = "table"
  elif return_format == "objects" or format_str == "objects":
    style = "objects"

  data = reshape_data(cur, fields, field_to_cols, style)

  if return_json:
    return jsonify({
      "data": data,
      "lastPage": None
    })
  else:
    return data

def reshape_data(rows, fields, field_to_cols=None, style="table"):

  # We may need to translate db columns --> field names.
  if field_to_cols is not None:
    cols_to_field = {v: k for k, v in field_to_cols.iteritems()}
  else:
    cols_to_field = {v: v for v in fields}

  if style=="objects":
    data = rows_to_objects(rows, fields, cols_to_field) 
  else: #assume style = "table"
    data = rows_to_arrays(rows, fields, cols_to_field)

  return data 


def rows_to_arrays(cur, fields, cols_to_field):
  data = OrderedDict()
  for i, row in enumerate(cur):
    for col in fields:
      # Some of the database column names don't match field names.
      field = cols_to_field.get(col, col)
      val = row[col]
      if isinstance(val, dict):
        for k, v in val.iteritems():
          if k not in data:
            data[k] = [None] * i
            data[k].append(v)
      else:
        data.setdefault(field,[]).append(row[col])
  if not data:
    #No data was found so fill with empty arrays
    for col in fields:
      data[col] = []
  return data

def rows_to_objects(cur, fields, cols_to_field):
    data = []
    for row in cur:
      rowdict = dict(row)
      finaldict = dict()

      # User may have requested only certain fields
      for col in fields:
        # Translate from database column to field name
        field = cols_to_field.get(col, col)
        finaldict[field] = rowdict[col]

      data.append(finaldict)
    return data
    

@app.route("/status",methods = ["GET"])
def status():
  info = dict()

  # Current branch
  info["branch"] = check_output("git symbolic-ref --short -q HEAD",shell=True).strip()

  # Current commit
  info["githash"] = check_output("git rev-parse HEAD",shell=True).strip()

  # Uptime
  minutes, seconds = divmod(time.time() - START_TIME,60)
  hours, minutes = divmod(minutes,60)
  days, hours = divmod(hours,24)
  days, hours, minutes, seconds = map(int,(days,hours,minutes,round(seconds)))
  info["uptime"] = "{}d:{}h:{}m:{}s".format(days,hours,minutes,seconds)

  return jsonify(info)

@app.route(
  "/v{}/annotation/recomb/".format(app.config["API_VERSION"]),
  methods = ["GET"]
)
def recomb():
  # Database columns and table
  db_table = "rest.recomb"
  db_cols = ["id","name","build","version"]

  return std_response(db_table,db_cols)

  
@app.route(
  "/v{}/annotation/recomb/results/".format(app.config["API_VERSION"]),
  methods = ["GET"]
)
def recomb_results():
  # Database columns and table
  db_table = "rest.recomb_results"
  db_cols = ["id", "chromosome", "position", "recomb_rate", "pos_cm"]

  filter_str = request.args.get("filter")
  fp = FilterParser()
  matches = fp.parse(filter_str)
  lrm = fp.left_middle_right(matches)

  sql_complier = SQLCompiler()
  def fetch(terms, limit=None):
    sql, params = sql_complier.to_sql_parsed(terms, db_table, db_cols, limit=limit)
    rows = g.db.execute(text(sql),params).fetchall()
    return rows
  
  def interp(at, left, right):
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

  if len(left)<1:
    left = [{"id": "chrleft", "position": lrm["range"]["left"], 
        "chromosome": lrm["range"]["chrom"], "recomb_rate": 0, "pos_cm": 0}]
  if len(right)<1:
    right = [{"id": "chrright", "position": lrm["range"]["right"], 
        "chromosome": lrm["range"]["chrom"], "recomb_rate": 0, "pos_cm": 0}]
  
  if len(middle)>0:
    left_end = interp(lrm["range"]["left"], left[0], middle[0])
    right_end = interp(lrm["range"]["right"], middle[-1], right[0])
  else:
    left_end = interp(lrm["range"]["left"], left[0], right[0])
    right_end = interp(lrm["range"]["right"], left[0], right[0])

  data = reshape_data([left_end] + middle + [right_end], db_cols)
  return jsonify({
    "data": data,
    "lastPage": None
  })

@app.route(
  "/v{}/annotation/intervals/".format(app.config["API_VERSION"]),
  methods = ["GET"]
)
def intervals():
  db_table = "rest.interval"
  db_cols = "id study build version type assay tissue protein histone cell_line pmid description url".split()

  return std_response(db_table,db_cols)

@app.route(
  "/v{}/annotation/intervals/results/".format(app.config["API_VERSION"]),
  methods = ["GET"]
)
def interval_results():
  db_table = "rest.interval_results"
  db_cols = "id public_id chrom start end strand annotation".split()

  field_to_col = dict(
    chromosome = "chrom"
  )

  return std_response(db_table,db_cols,field_to_col)

@app.route(
  "/v{}/statistic/single/".format(app.config["API_VERSION"]),
  methods = ["GET"]
)
def single():
  db_table = "rest.single_analyses"
  db_cols = "id study trait tech build imputed analysis pmid date first_author last_author".split()

  # For some reason, this database table has columns that don't match the field names in the filter string.
  # field_to_col = dict(
    # analysis = "id"
  # )

  return std_response(db_table,db_cols)

@app.route(
  "/v{}/statistic/single/results/".format(app.config["API_VERSION"]),
  methods = ["GET"]
)
def single_results():
  db_table = "rest.single_analyses_results"
  db_cols = "analysis_id variant_name chromosome position ref_allele_freq ref_allele p_value log_pvalue score_test_stat".split()

  # For some reason, this database table has columns that don't match the field names in the filter string.
  field_to_col = dict(
    analysis = "analysis_id",
    variant = "variant_name",
    pvalue = "p_value"
  )

  return std_response(db_table,db_cols,field_to_col)

@app.route(
  "/v{}/statistic/pair/LD/results/".format(app.config["API_VERSION"]),
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
  ld_cache = RedisIntervalCache(redis_client)

  # Cache key for this particular request.
  # Note that in Daniel's API, for now, "reference" is implicitly
  # attached to build, reference panel, and population all at the same time.
  # In the future, it will hopefully expand to accepting paramters for all 3, and
  # then we can include this in the cache key.
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
  max_flank = app.config["LD_MAX_FLANK"]
  if abs(refpos - start) > max_flank or abs(refpos - end) > max_flank:
    raise FlaskException("Distance requested from refsnp for LD calculation too far",413)

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
  try:
    cache_data = ld_cache.retrieve(cache_key,start,end)
  except:
    print "Warning: cache retrieval failed, traceback was: "
    traceback.print_exc()
    cache_data = None

  if cache_data is None:
    # Need to compute. Either the range given is larger than we've previously computed,
    # or redis is down.
    print "Cache miss for {reference}__{refvariant} in {start}-{end} ({rlength:,.2f}kb), recalculating".format(
      reference=reference,
      refvariant=refvariant,
      start=start,
      end=end,
      rlength=rlength/1000
    )

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

    try:
      ld_cache.store(cache_key,start,end,for_cache)
    except:
      print "Warning: storing data in cache failed, traceback was: "
      traceback.print_exc()

  else:
    print "Cache *match* for {reference}__{refvariant} in {start}-{end} ({rlength:,.2f}kb), using cached data".format(
      reference=reference,
      refvariant=refvariant,
      start=start,
      end=end,
      rlength=rlength/1000
    )

    # We can just use the cache's data directly.
    for position, ld_pair in iteritems(cache_data):
      data["chromosome2"].append(chromosome)
      data["position2"].append(position)
      data["rsquare"].append(JSONFloat(ld_pair["rsquare"]))
      data["variant2"].append(ld_pair["name2"])

  final_resp = jsonify(outer)

  return final_resp

@app.route(
  "/v{}/annotation/genes/".format(app.config["API_VERSION"]),
  methods = ["GET"]
)
def genes():
  db_table = "rest.genes"
  db_cols = "source_id gene_id gene_name chromosome interval_start interval_end strand".split()

  # Translate filter string "fields" to database column names
  field_to_col = dict(
    source = "source_id",
    start = "interval_start",
    end = "interval_end",
    chrom = "chromosome"
  )

  # This is used to translate database column names into the names expected in the response
  # Unfortunately this is highly inconsistent, but it's in production
  response_names = {
    "exon_end": "end",
    "exon_start": "start",
    "exon_strand": "strand",
    "transcript_strand": "strand",
    "transcript_start": "start",
    "transcript_end": "end"
  }

  # Does the user want transcripts?
  transcripts_arg = request.args.get("transcripts")
  do_transcripts = True if transcripts_arg is None or transcripts_arg.lower() in ("t","true") else False

  dgenes = {}
  genes_array = std_response(db_table,db_cols,field_to_col,return_json=False,return_format="objects")
  for i, gene_data in enumerate(genes_array):
    gene = Gene(**gene_data)
    dgenes[gene_data["gene_id"]] = gene
    genes_array[i] = gene

  # Which source IDs were requested? May need this for requesting transcripts/exons, if the user wants them.
  fp = FilterParser()
  params = fp.statements(request.args.get("filter"))
  sources_tmp = params["source"].value

  # Check each source to make sure it's an integer / sanitize user input
  sources = []
  for i in sources_tmp:
    try:
      i = int(i)
    except:
      continue

    sources.append(i)

  if len(sources) == 0:
    raise FlaskException("No valid sources specified in filter string",400)

#  api_internal_dev=# select * from rest.sp_transcripts_exons('{ENSG00000116649.9,ENSG00000148737.16}'::VARCHAR[],'{1}'::INT[]);
#  source_id |      gene_id      |   transcript_id   | transcript_name | transcript_chrom | transcript_start | transcript_end | transcript_strand |      exon_id      | exon_start | exon_end | exon_strand
# -----------+-------------------+-------------------+-----------------+------------------+------------------+----------------+-------------------+-------------------+------------+----------+-------------
#          1 | ENSG00000116649.9 | ENST00000376957.6 | SRM-001         | 1                |         11054589 |       11060024 | -                 | ENSE00000743124.1 |   11055781 | 11055926 | -
#          1 | ENSG00000116649.9 | ENST00000376957.6 | SRM-001         | 1                |         11054589 |       11060024 | -                 | ENSE00000743131.1 |   11059225 | 11059345 | -
#          1 | ENSG00000116649.9 | ENST00000376957.6 | SRM-001         | 1                |         11054589 |       11060024 | -                 | ENSE00001836529.1 |   11059777 | 11060024 | -

  if do_transcripts:
    # They want transcripts and exons included in the results.
    cur = g.db.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.callproc(
      "rest.sp_transcripts_exons",
      [
        dgenes.keys(),
        sources
      ]
    )

    dtranscripts = {}
    for row in cur.fetchall():
      row = dict(row)
      tsid = row["transcript_id"]
      geneid = row["gene_id"]
      chrom = row["transcript_chrom"]

      # Pull out transcript
      transcript = dtranscripts.get(tsid,None)
      if transcript is None:
        # We've never seen this transcript before. Create it, and add it to the proper gene.
        transcript_data = {response_names.get(k,k): v for k, v in row.iteritems() if k in "transcript_id transcript_name transcript_chrom transcript_start transcript_end transcript_strand".split()}
        transcript = Transcript(**transcript_data)

        dtranscripts[tsid] = transcript
        dgenes[geneid].add_transcript(transcript)

      # Pull out exon
      exon_data = {response_names.get(k,k): v for k, v in row.iteritems() if k in "exon_id exon_start exon_end exon_strand".split()}
      exon_data["chrom"] = chrom
      exon = Exon(**exon_data)

      # Add exon to transcript
      transcript.add_exon(exon)

      # Add exon to gene (the gene will end up with a list of all possible exons)
      dgenes[geneid].add_exon(exon)

  json_genes = [gg.to_dict() for gg in genes_array]

  outer = {
    "data": json_genes,
    "lastPage": None
  }

  return jsonify(outer)


@app.route(
  "/v{}/annotation/omnisearch/".format(app.config["API_VERSION"]),
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
        sql_complier = SQLCompiler()
        fields = ["source_id", "chromosome", "gene_name", "gene_id", "interval_start", "interval_end"]
        db_table = "rest.genes"
        sort_fields = ["chromosome","interval_start"]
        db_cols = "source_id gene_id gene_name chromosome interval_start interval_end strand".split()
        sql, params = sql_complier.to_sql(filter_str, db_table, db_cols, fields, sort_fields, None)
        cur = g.db.execute(text(sql), params)
        results = cur.fetchmany(2)
        if len(results)==1:
            row = results[0]
            x["chrom"] = row["chromosome"]
            x["start"] = row["interval_start"] - x.get("offset", 0)
            x["end"] = row["interval_end"] + x.get("offset", 0)
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
