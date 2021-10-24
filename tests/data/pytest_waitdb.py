#!/usr/bin/env python3
from argparse import ArgumentParser
from glob import glob
import os
import sys
import gzip
import psycopg2
import time

# This script can be used to initialize a test database for use with the
# test cases in the LocusZoom API. Please note this script will nuke the
# test database you specify with the --database argument.

def get_settings():
  p = ArgumentParser()
  p.add_argument("--connect-db")
  p.add_argument("--port")
  p.add_argument("--host")
  p.add_argument("--user")
  p.add_argument("--password")
  p.add_argument("--retries", default=10, help="Number of times to retry database.")
  p.add_argument("--interval", default=3, help="Time to wait between retries.")

  args = p.parse_args()

  args.host = args.host if args.host is not None else os.environ["POSTGRES_HOST"]
  args.port = args.port if args.port is not None else os.environ["POSTGRES_PORT"]
  args.user = args.user if args.user is not None else os.environ["POSTGRES_USER"]
  args.password = args.password if args.password is not None else os.environ.get("POSTGRES_PASSWORD")
  args.connect_db = args.connect_db if args.connect_db is not None else os.environ["POSTGRES_CONNECT_DB"]

  return args

if __name__ == "__main__":
  args = get_settings()

  # Connect to postgres and create the database.
  found = False
  for _ in range(args.retries):
    try:
      print("Trying to connect to postgres to check if database is up...")
      init_con = psycopg2.connect(database=args.connect_db, host=args.host, port=args.port, user=args.user, password=args.password)
    except:
      print("Database did not respond, waiting to retry...")
      time.sleep(args.interval)
    else:
      print("Database appears to be online")
      found = True
      break

  if not found:
    print("Failed to find database after {} retries.".format(args.retries))
    sys.exit(1)
