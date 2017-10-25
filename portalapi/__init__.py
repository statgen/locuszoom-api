import os, datetime
from flask import Flask
from flask.ext.cors import CORS
from flask.ext.cache import Cache
from flask.json import JSONEncoder
from raven.contrib.flask import Sentry

# Create flask app
app = Flask(__name__)

# Modified JSON encoder to handle datetimes
class CustomJSONEncoder(JSONEncoder):
  def default(self,x):
    if isinstance(x,(datetime.date,datetime.datetime)):
      return x.isoformat()

    return JSONEncoder.default(self,x)

app.json_encoder = CustomJSONEncoder

# Which config to use
mode = os.environ.get("PORTALAPI_MODE")
if mode is None:
  raise Exception("No API mode designated. Set the PORTALAPI_MODE environment variable to 'dev' or 'prod'")

# Config file given mode
config_file = os.path.join(app.root_path,"../etc/config-{}.py".format(mode))
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

# Start logging errors
sentry = Sentry(app,dsn=app.config["SENTRY_DSN"],register_signal=False,wrap_wsgi=False)

from portalapi.controllers import routes
