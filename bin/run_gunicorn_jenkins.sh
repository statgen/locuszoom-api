#!/bin/bash
export PORTALAPI_MODE="jenkins"
mkdir -p logs
gunicorn -k gevent -w 2 -b 127.0.0.1:7325 portalapi:app \
  --access-logfile logs/gunicorn.${PORTALAPI_MODE}.access.log \
  --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" [reqtime: %(L)ss] -- %(U)s -- %(q)s' \
  --error-logfile logs/gunicorn.${PORTALAPI_MODE}.error.log \
  --log-level info

