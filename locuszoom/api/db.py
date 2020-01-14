from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from flask import current_app, g
#import psycopg2
#import math

#def handle_float(value, cur):
  #"""
  #Translate real/double precision values from database into valid JSON.
  #"""

  #if value == "Infinity":
    #return "Infinity"
  #elif value == "-Infinity":
    #return "-Infinity"
  #elif value is None:
    #return None
  #else:
    #return float(value)

def before_request():
  db = getattr(g,"db",None)
  if db is None:
    # Create SQLalchemy engine
    engine = create_engine(
      URL(**current_app.config["DATABASE"]),
      connect_args = dict(
        application_name = current_app.config["DB_APP_NAME"]
      ),
      pool_size = 5,
      max_overflow = 0,
      isolation_level = "AUTOCOMMIT"
      # poolclass = NullPool
    )

    # Create database connection
    db = engine.connect()

  # Assign to app context
  g.db = db

  # Hard coded for now - should look up from DB
  build_id = getattr(g, "build_id", None)
  if build_id is None:
    build_id = {"grch37": {"db_snp": 16, "genes": 2},
        "grch38": {"db_snp": 17, "genes": 1}}
    g.build_id = build_id

def close_db(*args):
  db = g.pop("db",None)
  if db is not None:
    db.close()

def init_app(app):
  app.before_request(before_request)
  app.teardown_appcontext(close_db)

  # Map real (OID 700) and double precision (OID 701) to float type that parses correctly for JSON format
  #float_json = psycopg2.extensions.new_type((700, 701), "FLOAT_JSON", handle_float)
  #psycopg2.extensions.register_type(float_json)
