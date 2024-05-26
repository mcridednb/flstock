import logging
import os
import sys
import warnings

from dotenv import load_dotenv
from loguru import logger


class LoguruHandler(logging.Handler):
    def emit(self, record):
        logging.getLogger(record.name).handle(record)


load_dotenv()

logging.disable(logging.DEBUG)
LOG_LEVEL = logging.getLevelName(logging.CRITICAL)
warnings.filterwarnings("ignore")

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger.remove()
log_format = (
    "<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
)
logger.add(LoguruHandler(), format=log_format, level="DEBUG")

BOT_NAME = "flstock"

SPIDER_MODULES = ["spiders"]
NEWSPIDER_MODULE = "spiders"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = "flstock (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "middlewares.FlstockSpiderMiddleware": 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "middlewares.StatusMiddleware": 50,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "pipelines.MongoPipeline": 300,
    "pipelines.CeleryPipeline": 400,
    # "pipelines.FlstockPipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# PROXY
PROXY_URL = os.getenv("PROXY_URL")
PROXY_REBOOT_URL = os.getenv("PROXY_REBOOT_URL")

# KWORK
KWORK_LOGIN = os.getenv("KWORK_LOGIN")
KWORK_PASSWORD = os.getenv("KWORK_PASSWORD")
KWORK_PHONE_LAST = os.getenv("KWORK_PHONE_LAST")

# FL
FL_LOGIN = os.getenv("FL_LOGIN")
FL_PASSWORD = os.getenv("FL_PASSWORD")
FL_CLIENT_ID = os.getenv("FL_CLIENT_ID")

# MongoDB
MONGO_URI = os.getenv("MONGO_URI")

# Postgres
POSTGRES_URI = "postgresql+psycopg2://{}:{}@{}:{}/{}".format(
    os.getenv("POSTGRES_USER"),
    os.getenv("POSTGRES_PASSWORD"),
    os.getenv("POSTGRES_HOST"),
    os.getenv("POSTGRES_PORT"),
    os.getenv("POSTGRES_DB"),
)

# RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT")
RABBITMQ_USERNAME = os.getenv("RABBITMQ_DEFAULT_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_DEFAULT_PASS")

RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE")

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
