import sys

from dotenv import load_dotenv
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

logger.remove()
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS!UTC}</green> | "
    "<level>{level}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)
logger.add(sys.stdout, format=log_format)
logger.add(
    f"logs/bot.log",
    format=log_format,
    rotation="10 MB",
    compression="zip",
    enqueue=True,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False)
    redis_host: str
    redis_port: int
    webhook_secret: str
    base_webhook_url: str
    telegram_bot_token: str
    web_server_host: str = "0.0.0.0"
    web_server_port: int = 8888
    webhook_path: str = "/webhook"
    yookassa_account_id: str
    yookassa_secret_key: str


settings = Settings()
