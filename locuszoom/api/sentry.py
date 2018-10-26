from raven.contrib.flask import Sentry

def init_app(app):
  # Start logging errors
  sentry = None
  if "SENTRY_DSN" in app.config:
    print("Sentry DSN found, attaching to app")
    sentry = Sentry(app,dsn=app.config["SENTRY_DSN"],register_signal=False,wrap_wsgi=False)
  else:
    print("Warning: Sentry DSN not found, skipping")

  app.sentry = sentry
