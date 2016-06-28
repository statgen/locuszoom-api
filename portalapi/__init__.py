import os
from flask import Flask
from flask.ext.cors import CORS
from flask.ext.cache import Cache

# Create flask app
app = Flask(
  __name__,
  instance_relative_config = True
)

# Which config to use
mode = os.environ.get("PORTALAPI_MODE")
if mode is None:
  raise Exception, "No API mode designated. Set the PORTALAPI_MODE environment variable to 'dev' or 'prod'"
elif mode == "dev":
  print "Starting with development config..."
  app.config.from_object("portalapi.flask_cfg.DevConfig")
elif mode == "prod":
  print "Starting with production config..."
  app.config.from_object("portalapi.flask_cfg.ProdConfig")
elif mode == "quick":
  print "Starting with quick config..."
  app.config.from_object("portalapi.flask_cfg.QuickConfig")
else:
  raise Exception, "Unrecognized value for PORTALAPI_MODE: " + mode

# Enable cross-domain headers on all routes
CORS(app)

# Enable caching
cache = Cache(
  app,
  config = app.config["CACHE_CONFIG"]
)

import portalapi.views

