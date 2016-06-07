#!/bin/bash
export PORTALAPI_MODE="prod"
gunicorn -k gevent -w 32 -b 0.0.0.0:7500 portalapi:app
