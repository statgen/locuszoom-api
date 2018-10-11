import redis
from flask import current_app, g

def before_request():
  # Setup redis
  g.redis_client = redis.StrictRedis(
    host = current_app.config["REDIS_HOST"],
    port = current_app.config["REDIS_PORT"],
    db = current_app.config["REDIS_DB"]
  )

def init_app(app):
  app.before_request(before_request)
