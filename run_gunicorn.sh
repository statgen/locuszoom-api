#!/bin/bash
export PORTALAPI_MODE="prod"
gunicorn -k gevent -w 4 -b 0.0.0.0:7500 portalapi:app
