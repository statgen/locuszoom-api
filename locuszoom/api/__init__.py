import os, datetime
from flask import Flask
from flask.ext.cors import CORS
from flask.ext.cache import Cache
from flask.json import JSONEncoder
from raven.contrib.flask import Sentry

# Modified JSON encoder to handle datetimes
class CustomJSONEncoder(JSONEncoder):
  def default(self,x):
    if isinstance(x,(datetime.date,datetime.datetime)):
      return x.isoformat()

    return JSONEncoder.default(self,x)

def create_app():
  # Create flask app
  app = Flask(__name__)

  # Which config to use
  mode = os.environ.get("LZAPI_MODE")
  if mode is None:
    raise Exception("No API mode designated. Set the LZAPI_MODE environment variable to 'dev' or 'prod'")

  # Config file given mode
  config_file = os.path.join(app.root_path,"../../etc/config-{}.py".format(mode))
  if not os.path.isfile(config_file):
    raise IOError("Could not find configuration file {} for API mode {}".format(config_file,mode))

  # Load config
  app.config.from_pyfile(config_file)

  # Start logging errors
  sentry = None
  if "SENTRY_DSN" in app.config:
    sentry = Sentry(app,dsn=app.config["SENTRY_DSN"],register_signal=False,wrap_wsgi=False)
  else:
    print "Warning: Sentry DSN not found, skipping"

  # Enable cross-domain headers on all routes
  CORS(app)

  # Enable caching
  cache = Cache(
    app,
    config = app.config["CACHE_CONFIG"]
  )

  # Register routes with app
  with app.app_context():
    from locuszoom.api import routes
    app.register_blueprint(routes.bp)

  # JSON encoder for datetimes
  app.json_encoder = CustomJSONEncoder

  return app
