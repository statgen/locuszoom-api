PROPAGATE_EXCEPTIONS = True
API_VERSION = 1

# Flask settings
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 7700

# Database
DATABASE = dict(
  drivername = "postgresql",
  host = "localhost",
  port = "5432",
  username = "postgres",
  database = "travis"
)

# Redis settings
REDIS_HOST = "localhost"
REDIS_PORT = "6379"
REDIS_DB = 3

# Name passed along to Postgres for application_name
DB_APP_NAME = "locuszoom-api-travis"

# Cache settings
CACHE_CONFIG = dict(
  CACHE_TYPE = "filesystem",
  CACHE_DIR = "/data/locuszoom-api-cache/travis",
  CACHE_THRESHOLD = 5000,
  CACHE_DEFAULT_TIMEOUT = 2592000 # 30 days
)

# Maximum LD window size
LD_MAX_SIZE = int(4E6)
