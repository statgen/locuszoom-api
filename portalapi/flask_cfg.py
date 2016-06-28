#!/usr/bin/env python

class BaseConfig(object):
  pass

class DevConfig(BaseConfig):
  # API version
  API_VERSION = 1

  # Database
  DATABASE = dict(
    drivername = "postgres",
    host = "localhost",
    port = "5432",
    username = "portaldev_user",
    password = "portaldev_user",
    database = "api_internal_dev"
  )

  # Name passed along to Postgres for application_name
  DB_APP_NAME = "portalapi-flaskdbg"

  # Flask settings
  PROPAGATE_EXCEPTIONS = True

  # Cache settings
  CACHE_CONFIG = dict(
    CACHE_TYPE = "filesystem",
    CACHE_DIR = "/home/welchr/projects/api_flask/portalapi/cache/dev/",
    CACHE_THRESHOLD = 1000,
    CACHE_DEFAULT_TIMEOUT = 2592000 # 30 days
  )

class ProdConfig(BaseConfig):
  # API version
  API_VERSION = 1

  # Database
  DATABASE = dict(
    drivername = "postgres",
    host = "localhost",
    port = "5432",
    username = "portaldev_user",
    password = "portaldev_user",
    database = "api_internal_dev"
  )

  # Name passed along to Postgres for application_name
  DB_APP_NAME = "portalapi-flask"

  # Flask settings
  PROPAGATE_EXCEPTIONS = True

  # Cache settings
  CACHE_CONFIG = dict(
    CACHE_TYPE = "filesystem",
    CACHE_DIR = "/home/welchr/projects/api_flask/portalapi/cache/prod/",
    CACHE_THRESHOLD = 5000,
    CACHE_DEFAULT_TIMEOUT = 2592000 # 30 days
  )

class QuickConfig(BaseConfig):
  # API version
  API_VERSION = 1

  # Database
  DATABASE = dict(
    drivername = "postgres",
    host = "localhost",
    port = "5432",
    username = "portaldev_user",
    password = "portaldev_user",
    database = "api_public_prod"
  )

  # Name passed along to Postgres for application_name
  DB_APP_NAME = "portalapi-flask"

  # Flask settings
  PROPAGATE_EXCEPTIONS = True

  # Cache settings
  CACHE_CONFIG = dict(
    CACHE_TYPE = "filesystem",
    CACHE_DIR = "/home/welchr/projects/api_flask/portalapi/cache/quick/",
    CACHE_THRESHOLD = 5000,
    CACHE_DEFAULT_TIMEOUT = 2592000 # 30 days
  )
