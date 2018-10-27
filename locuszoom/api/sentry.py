import os
from raven.contrib.flask import Sentry
from raven.versioning import fetch_git_sha
from flask import current_app

sentry = None

def get_sentry():
  global sentry

  # Start logging errors
  sha = fetch_git_sha(os.path.join(current_app.root_path,"../../"))
  release = f"locuszoom-api@{sha}"

  if sentry is None:
    if "SENTRY_DSN" in current_app.config:
      print("Sentry DSN found, attaching to app")
      current_app.config["SENTRY_CONFIG"] = {
        "dsn": current_app.config["SENTRY_DSN"],
        "release": release,
        "environment": current_app.config["LZAPI_MODE"]
      }
      sentry = Sentry(current_app,register_signal=False,wrap_wsgi=False)
    else:
      print("Warning: Sentry DSN not found, skipping")
  else:
    print("Sentry already attached to app")

  return sentry
