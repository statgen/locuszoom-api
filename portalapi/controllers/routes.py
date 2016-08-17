#!/usr/bin/env python
from collections import OrderedDict
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import URL
from flask import g, jsonify, request
from portalapi import app, cache
from portalapi.uriparsing import SQLCompiler, LDAPITranslator, FilterParser
from portalapi.models.gene import Gene, Transcript, Exon
from pyparsing import ParseException
import requests
import psycopg2

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

def get_db():
  return create_engine(
    URL(**app.config["DATABASE"]),
    connect_args = dict(
      application_name = app.config["DB_APP_NAME"]
    ),
    pool_size = 5,
    max_overflow = 0
    # poolclass = NullPool
  ).connect()

@app.before_request
def before_request():
  db = getattr(g,"db",None)
  if db is None:
    db = get_db()

  g.db = db

@app.teardown_appcontext
def close_db(*args):
  db = getattr(g,"db",None)
  if db is not None:
    db.close()

def std_response(db_table,db_cols,field_to_cols=None,return_json=True,return_format=None):
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

  # if filter_str is not None:
  #   sql, params = fparser.parse_into_sql(filter_str,db_table,db_cols,fields,sort_fields)
  # else:
  #   sql = "SELECT * FROM {}".format(db_table)
  #   params = []

  sql, params = sql_compiler.to_sql(filter_str,db_table,db_cols,fields,sort_fields,field_to_cols)

  # text() is sqlalchemy helper object when specifying SQL as plain text string
  # allows for bind parameters to be used
  cur = g.db.execute(text(sql),params)

  outer = {
    "data": None,
    "lastPage": None
  }

  # We may need to translate db columns --> field names.
  if field_to_cols is not None:
    cols_to_field = {v: k for k, v in field_to_cols.iteritems()}
  else:
    cols_to_field = {v: v for v in db_cols}

  # Figure out return format.
  if return_format == "table" or (return_format is None and (format_str is None or format_str == "")):
    data = OrderedDict()

    for i, row in enumerate(cur):
      for col in fields:
        # Some of the database column names don't match field names.
        field = cols_to_field.get(col,col)

        val = row[col]
        if isinstance(val,dict):
          for k, v in val.iteritems():
            if k not in data:
              data[k] = [None] * i

            data[k].append(v)
        else:
          data.setdefault(field,[]).append(row[col])

    outer["data"] = data

  elif return_format == "objects" or format_str == "objects":
    data = []
    for row in cur:
      rowdict = dict(row)
      finaldict = dict()

      # User may have requested only certain fields
      for col in fields:
        # Translate from database column to field name
        field = cols_to_field.get(col,col)
        finaldict[field] = rowdict[col]

      data.append(finaldict)

    outer["data"] = data

  if return_json:
    return jsonify(outer)
  else:
    return data

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
  db_cols = ["id","chromosome","position","recomb_rate","pos_cm"]

  return std_response(db_table,db_cols)

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

def make_cache_key(*args,**kwargs):
  return request.url

@app.route(
  "/v{}/statistic/pair/LD/results/".format(app.config["API_VERSION"]),
  methods = ["GET"]
)
@cache.cached(key_prefix=make_cache_key)
def ld_results():
  print "Cache miss, calculating LD for request: {}".format(request.url)

  # GET request parameters
  filter_str = request.args.get("filter")
  fields_str = request.args.get("fields")
  sort_str = request.args.get("sort")
  format_str = request.args.get("format")

  if filter_str is None:
    raise FlaskException("No filter string specified",400)

  # Figure out the LD API URL to send the request through
  #base_url = "http://localhost:8888/api_ld/ld?"
  base_url = "http://portaldev.sph.umich.edu/api_ld/ld?"
  trans = LDAPITranslator()
  param_str = trans.to_refsnp_url(filter_str)
  final_url = base_url + param_str

  # Fire off the request to the LD server.
  try:
    resp = requests.get(final_url)
  except Exception as e:
    raise FlaskException("Failed retrieving data from LD server, error was {}".format(e.message),500)

  # Did it come back OK?
  if not resp.ok:
    raise FlaskException("Failed retrieving data from LD server, error was {}".format(resp.reason),500)

  ld_json = resp.json()
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

  for obj in ld_json["pairs"]:
    data["chromosome2"].append(ld_json["chromosome"])
    data["position2"].append(obj["position2"])
    data["rsquare"].append(obj["rsquare"])
    data["variant2"].append(obj["name2"])

  outer["data"] = data

  return jsonify(outer)

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
