#!/bin/bash
export PORTALAPI_MODE="dev"
gunicorn -k gevent -w 12 -b 0.0.0.0:7600 portalapi:app
