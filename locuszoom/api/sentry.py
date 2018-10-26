import os
from raven.contrib.flask import Sentry
from raven.versioning import fetch_git_sha

def init_app(app):
  # Start logging errors
  sentry = None

  sha = fetch_git_sha(os.path.join(app.root_path,"../../"))
  release = f"locuszoom-api@{sha}"

  if "SENTRY_DSN" in app.config:
    print("Sentry DSN found, attaching to app")
    app.config["SENTRY_CONFIG"] = {
      "dsn": app.config["SENTRY_DSN"],
      "release": release,
      "environment": app.config["LZAPI_MODE"]
    }
    sentry = Sentry(app,register_signal=False,wrap_wsgi=False)
  else:
    print("Warning: Sentry DSN not found, skipping")

  app.sentry = sentry
