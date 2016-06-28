#!/bin/bash
export PORTALAPI_MODE="prod"
gunicorn -k gevent -w 12 -b 0.0.0.0:7500 portalapi:app \
  --access-logfile gunicorn.prod.access.log \
  --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" [reqtime: %(L)ss] -- %(U)s -- %(q)s' \
  --error-logfile gunicorn.prod.error.log \
  --log-level info

