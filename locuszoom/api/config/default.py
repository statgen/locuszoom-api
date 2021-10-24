PROPAGATE_EXCEPTIONS = True
API_VERSION = 1

# Database
DATABASE = dict(
  drivername = "postgres",
  host = "localhost",
  port = "5432",
  username = "user",
  password = "pass",
  database = "devdb"
)

# Redis settings
REDIS_HOST = "localhost"
REDIS_PORT = "6379"
REDIS_DB = 1

# Name passed along to Postgres for application_name
DB_APP_NAME = "locuszoom-api-dev-server"

# Cache settings
CACHE_CONFIG = dict(
  CACHE_TYPE = "filesystem",
  CACHE_DIR = "/path/to/your/cache",
  CACHE_THRESHOLD = 1000,
  CACHE_DEFAULT_TIMEOUT = 2592000 # 30 days
)

# Maximum distance from a reference variant that we will allow
# for LD calculations
LD_MAX_FLANK = int(3E6)

# Maximum number of records that can be retrieved at once.
MAX_RECORDS = 100000
