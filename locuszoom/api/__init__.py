import os, datetime, logging
from flask import Flask, g
from flask_cors import CORS
from flask_compress import Compress
from locuszoom.api.jsonutil import CustomJSONEncoder

def create_app():
  # Create flask app
  app = Flask(__name__)

  # Which config to use
  lzapi_mode = os.environ.get("LZAPI_MODE")
  if lzapi_mode is None:
    raise Exception("No API mode designated. Set the LZAPI_MODE environment variable to 'dev' or 'prod'")

  # Config file given mode
  config_file = os.path.join(app.root_path,"../../etc/config-{}.py".format(lzapi_mode))
  if not os.path.isfile(config_file):
    raise IOError("Could not find configuration file {} for API mode {}".format(config_file,lzapi_mode))

  # Load config
  app.config.from_pyfile(config_file)

  # Set mode
  app.config["LZAPI_MODE"] = lzapi_mode

  # Enable cross-domain headers on all routes
  CORS(app)

  # Enable compression support
  Compress(app)

  # Setup Postgres DB
  from . import db
  db.init_app(app)

  # Setup redis
  from . import redis_client
  redis_client.init_app(app)

  # Setup helpers
  from . import helpers
  helpers.init_app(app)

  # Setup error handlers
  from . import errors
  errors.init_app(app)

  # Register routes with app
  with app.app_context():
    from . import routes
    app.register_blueprint(routes.bp)

  # JSON encoder for datetimes
  app.json_encoder = CustomJSONEncoder

  # If gunicorn is attached, route loggers there
  try:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
  except Exception as e:
    app.logger.warning("Could not attach to gunicorn logger: " + str(e))

  app.logger.info("Flask app initialized")

  return app
