import traceback
import re
from flask import current_app, request, jsonify
from pyparsing import ParseException
from locuszoom.api.sentry import get_sentry

class FlaskException(Exception):
  status_code = 400

  def __init__(self, message, status_code=None, payload=None):
    Exception.__init__(self)
    self.message = message
    if status_code is not None:
      self.status_code = status_code
    self.payload = payload

  def to_dict(self):
    rv = dict(self.payload or ())
    rv['message'] = self.message
    return rv

def handle_all(error):
  # Log all exceptions to Sentry
  # If this is a jenkins testing instance, though, don't log to Sentry (we'll see
  # these exceptions in the jenkins console)
  sentry = get_sentry()
  if current_app.config["LZAPI_MODE"] != "travis":
    if sentry is not None:
      print("Attempting to log exception to Sentry...")
      sentry.captureException()
    else:
      print("Warning: Sentry not setup to log exception")

  # If we're in debug mode, re-raise the exception so we get the
  # browser debugger
  if current_app.debug:
    raise

  # Also log the exception to the console.
  current_app.logger.error("Exception thrown while handling request: " + request.url)
  if isinstance(error,Exception):
    current_app.logger.error("Exception type: " + str(type(error)))
    current_app.logger.error("Exception message: " + str(error))
    current_app.logger.error("Exception traceback: ")
    current_app.logger.error("".join((traceback.format_tb(error.__traceback__))))

  if isinstance(error,ParseException):
    message = "Incorrect syntax in filter string, error was: " + error.msg
    code = 400
  elif isinstance(error,FlaskException):
    message = error.message
    code = error.status_code
  else:
    message = "An exception was thrown while handling the request. If you believe this request should have succeeded, please create an issue: https://github.com/statgen/locuszoom-api/issues"
    code = 500

  # A little extra work to figure out the true request URL.
  # Requires the following set in apache:
  #   SetEnvIf Request_URI "^(.*)$" REQUEST_URI=$1
  #   RequestHeader set X-Request-Uri "%{REQUEST_URI}e"
  full_url = request.url
  real_uri = request.headers.get("X-Request-Uri")
  if real_uri is not None:
    match = re.search("\/(?P<api>\w+)\/(?P<version>v\d+)",real_uri)
    if match:
      api_name, api_version = match.groups()
      full_url = full_url.replace("/" + api_version,"/" + api_name + "/" + api_version)

  response = jsonify({
    "message": message,
    "request": full_url
  })
  response.status_code = code
  return response

def init_app(app):
  app.register_error_handler(Exception,handle_all)
