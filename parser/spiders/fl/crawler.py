import os
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urljoin, urlencode

import redis
import scrapy
from dotenv import load_dotenv
from loguru import logger
from pydantic import Field, field_validator

from spiders.fl.constants import SUBCATEGORIES_REVERSE
from spiders.models import ExtraMixin
from spiders.utils import start_crawl

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)


class Project(ExtraMixin):
    project_id: int = Field(alias="id")
    price: Optional[int] = Field(alias="cost")
    title: str = Field(alias="name")
    description: str
    source: str = Field(default="fl")
    offers: int = Field(alias="offer_count")
    order_created: int = Field(alias="created_at")
    url: str
    category: Optional[str] = None
    subcategory: Optional[str] = Field(alias="professions")
    currency_symbol: str
    price_max: Optional[int] = None

    @field_validator("subcategory", mode="before")
    def parse_subcategory(cls, value):
        if value:
            subcategory = SUBCATEGORIES_REVERSE.get(value[0]["id"])
            if not subcategory:
                logger.error(f"Unknown subcategory: {value}")
            return subcategory

    @field_validator("order_created", mode="before")
    def parse_order_created(cls, value):
        if value:
            return value / 1000.0

    @field_validator("price", mode="before")
    def parse_price(cls, value):
        if value:
            return int(value.get("amount", 0)) or None

    def get_id(self):
        return f"{self.source}_{self.project_id}"

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        data["_id"] = self.get_id()
        data["last_update"] = datetime.now()
        return data


class FLSpider(scrapy.Spider):
    name = "fl"
    allowed_domains = ["fl.ru"]
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 1,
        "URLLENGTH_LIMIT": 100000,
    }
    CURRENCY_SYMBOL = "₽"
    BASE_URL = "https://api.fl.ru"
    LOGIN_URL = urljoin(BASE_URL, "v1/login")
    PROJECTS_URL = urljoin(BASE_URL, "v1/projects")

    HEADERS = {
        "User-Agent": "android",
        "Accept-Encoding": "gzip, deflate, br",
        "Host": "api.fl.ru",
        "Connection": "keep-alive",
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._token = None

    def start_parsing(self):
        current_time = datetime.now()
        since = int((current_time - timedelta(minutes=10)).timestamp() * 1000)
        params = {
            "offset": 0,
            "limit": 20,
            "since": since,
            "without_executor": 1,
        }
        url = f"{self.PROJECTS_URL}?{urlencode(params)}"
        yield scrapy.Request(
            url=url,
            method="GET",
            callback=self.parse_projects,
            headers={
                **self.HEADERS,
                "Authorization": f"Bearer {self._token}"
            },
        )

    def start_requests(self):
        self._token = redis_client.get("fl_token")
        if not self._token:
            body = urlencode({
                "username": self.settings.get("FL_LOGIN"),
                "password": self.settings.get("FL_PASSWORD"),
                "client_id": self.settings.get("FL_CLIENT_ID"),
            })

            yield scrapy.Request(
                url=self.LOGIN_URL,
                method="POST",
                body=body,
                callback=self.parse_token,
                headers={
                    **self.HEADERS,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
        else:
            self._token = self._token.decode("utf-8")
            yield from self.start_parsing()

    def parse_token(self, response):
        self._token = response.json()["auth"]["token"]
        redis_client.set("fl_token", self._token)
        yield from self.start_parsing()

    def parse_projects(self, response):
        for row in response.json()["items"]:
            row["currency_symbol"] = self.CURRENCY_SYMBOL
            yield Project.parse_obj(row).dict()


if __name__ == "__main__":
    start_crawl(FLSpider)
