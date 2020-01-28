#!/usr/bin/env python3
from argparse import ArgumentParser
from glob import glob
import os
import gzip
import psycopg2

# This script can be used to initialize a test database for use with the
# test cases in the LocusZoom API. Please note this script will nuke the
# test database you specify with the --database argument.

def get_settings():
  p = ArgumentParser()
  p.add_argument("--connect-db")
  p.add_argument("--database")
  p.add_argument("--port")
  p.add_argument("--host")
  p.add_argument("--user")

  args = p.parse_args()

  args.host = args.host if args.host is not None else os.environ.get("POSTGRES_HOST")
  args.port = args.port if args.port is not None else os.environ.get("POSTGRES_PORT")
  args.user = args.user if args.user is not None else os.environ.get("POSTGRES_USER")
  args.connect_db = args.connect_db if args.connect_db is not None else os.environ.get("POSTGRES_CONNECT_DB")
  args.database = args.database if args.database is not None else os.environ.get("POSTGRES_TEST_DB")

  return args

if __name__ == "__main__":
  args = get_settings()

  # Connect to postgres and create the database.
  if args.connect_db is not None:
    init_con = psycopg2.connect(database=args.connect_db, host=args.host, port=args.port, user=args.user)
    init_con.autocommit = True
    init_cur = init_con.cursor()

    # Create the testing database, dropping it if it already exists.
    init_cur.execute(f"DROP DATABASE IF EXISTS {args.database}")
    init_cur.execute(f"CREATE DATABASE {args.database}")

  # Re-connect to the database.
  print(f"Connecting to PostgresDB - database {args.database} • host {args.host} • port {args.port} • user {args.user}")
  con = psycopg2.connect(database=args.database, host=args.host, port=args.port, user=args.user)
  con.autocommit = True
  cur = con.cursor()

  # Fire up the users, schema, tables.
  # with open("../create_users.sql") as fp:
    # code = fp.read()
    # cur.execute(code)

  with open("create_tables.sql") as fp:
    code = fp.read()
    cur.execute(code)

  with open("create_sp.sql") as fp:
    code = fp.read()
    cur.execute(code)

  # Load tables with data
  for f in glob("table_*.gz"):
    table = "rest." + f.replace("table_","").replace(".gz","")
    with gzip.open(f) as fp:
      cur.copy_from(fp, table)
