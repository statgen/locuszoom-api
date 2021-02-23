#!/usr/bin/env python3
import os

WORKER_COUNT = 4
THREAD_COUNT = 2

def import_settings(f):
  with open(f) as fp:
    code = compile(fp.read(),f,"exec")
    exec(code,globals())

def parse_args():
  from argparse import ArgumentParser
  p = ArgumentParser()
  p.add_argument("--mode")
  p.add_argument("--port",type=int)
  p.add_argument("--host",type=str)
  return p.parse_args()

def bash(cmd):
  from subprocess import Popen
  p = Popen(cmd,shell=True,executable="/bin/bash",universal_newlines=True)
  p.wait()

  if p.returncode != 0:
    raise Exception("Shell command `{}` failed with returncode {}".format(cmd,p.returncode))

if __name__ == "__main__":
  # What server mode?
  # Should be one of: prod, dev, jenkins, quick
  args = parse_args()
  mode = os.environ.get("LZAPI_MODE")
  if mode is None:
    mode = args.mode

  if mode is None:
    raise Exception("API mode must be set either with the envvar LZAPI_MODE, or with --mode")

  # Make sure the environment variable LZAPI_MODE is set
  # This is needed by the gunicorn command, the flask app,
  # and the find/monitor server code
  os.environ["LZAPI_MODE"] = mode

  # Load settings for this server mode
  # Importantly, FLASK_HOST and FLASK_PORT
  import_settings("etc/config-{}.py".format(mode))

  # Did we have a host/port specified on the command line, by jenkins maybe?
  # This will override what was given in the config file
  if args.port is not None:
    FLASK_PORT = args.port

  if args.host is not None:
    FLASK_HOST = args.host

  # Make directory for log files, if it doesn't exist
  bash("mkdir -p logs")

  # Fire up the gunicorn server
  bash(
    """

    gunicorn -k gthread --threads {threads} -w {workers} -b {host}:{port} 'locuszoom.api:create_app()' \
      --access-logfile logs/gunicorn.${{LZAPI_MODE}}.access.log \
      --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" [reqtime: %(L)ss] -- %(U)s -- %(q)s' \
      --error-logfile logs/gunicorn.${{LZAPI_MODE}}.error.log \
      --log-level info

    """.format(host=FLASK_HOST,port=FLASK_PORT,workers=WORKER_COUNT,threads=THREAD_COUNT)
  )

