import os
from flask import Flask
from flask.ext.cors import CORS
from flask.ext.cache import Cache

# Create flask app
app = Flask(__name__)

# Which config to use
mode = os.environ.get("PORTALAPI_MODE")
if mode is None:
  raise Exception("No API mode designated. Set the PORTALAPI_MODE environment variable to 'dev' or 'prod'")

# Config file given mode
config_file = "../etc/config-{}.py".format(mode)
if not os.path.isfile(config_file):
  raise IOError("Could not find configuration file {} for API mode {}".format(config_file,mode))

# Load config
app.config.from_pyfile(config_file)

# Enable cross-domain headers on all routes
CORS(app)

# Enable caching
cache = Cache(
  app,
  config = app.config["CACHE_CONFIG"]
)

from portalapi.controllers import routes
