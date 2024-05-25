import os
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlencode

import redis
import scrapy
from dotenv import load_dotenv
from loguru import logger
from pydantic import Field, field_validator

from spiders.kwork.constants import CATEGORIES, SUBCATEGORIES_REVERSE
from spiders.models import ExtraMixin
from spiders.utils import start_crawl

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)


class Project(ExtraMixin):
    project_id: int = Field(alias="id")
    price: int
    title: str
    description: str
    source: str = Field(default="kwork")
    offers: int
    order_created: int = Field(alias="date_confirm")
    category: str
    subcategory: str = Field(alias="category_id")
    currency_symbol: str
    price_max: Optional[int] = Field(alias="possible_price_limit")

    @field_validator("subcategory", mode="before")
    def parse_subcategory(cls, value):
        subcategory = SUBCATEGORIES_REVERSE.get(value)
        if not subcategory:
            logger.error(f"Unknown subcategory: {value}")
        return subcategory

    def get_id(self):
        return f"{self.source}_{self.project_id}"

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        data["_id"] = self.get_id()
        data["last_update"] = datetime.now()
        data["url"] = f"https://kwork.ru/projects/{self.project_id}"
        return data


class KworkSpider(scrapy.Spider):
    name = "kwork"
    allowed_domains = ["kwork.ru"]
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 1,
        "URLLENGTH_LIMIT": 100000,
    }
    CURRENCY_SYMBOL = "₽"
    BASE_URL = "https://api.kwork.ru"
    LOGIN_URL = urljoin(BASE_URL, "signIn")
    PROJECTS_URL = urljoin(BASE_URL, "projects")
    CATEGORIES_URL = urljoin(BASE_URL, "categories")

    HEADERS = {
        "Origin": "https://api.kwork.ru",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/68.0.3440.106 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://api.kwork.ru/",
        "Authorization": "Basic bW9iaWxlX2FwaTpxRnZmUmw3dw==",
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._token = None

    def start_parsing(self):
        for category_id, category in CATEGORIES.items():
            query_string = urlencode({
                "categories": category_id,
                "token": self._token,
            })
            url = f"{self.PROJECTS_URL}?{query_string}"
            yield scrapy.Request(
                url=url,
                method="POST",
                callback=self.parse_projects,
                headers=self.HEADERS,
                meta={
                    "category": category["code"],
                }
            )

    def start_requests(self):
        self._token = redis_client.get("kwork_token")
        if not self._token:
            query_string = urlencode({
                "login": self.settings.get("KWORK_LOGIN"),
                "password": self.settings.get("KWORK_PASSWORD"),
                "phone_last": self.settings.get("KWORK_PHONE_LAST"),
            })
            url = f"{self.LOGIN_URL}?{query_string}"
            yield scrapy.Request(
                url=url,
                method="POST",
                callback=self.parse_token,
                headers=self.HEADERS,
            )
        else:
            self._token = self._token.decode("utf-8")
            yield from self.start_parsing()

    def parse_token(self, response):
        self._token = response.json()["response"]["token"]
        redis_client.set("kwork_token", self._token)
        yield from self.start_parsing()

    def parse_projects(self, response):
        category = response.meta.get("category")

        for row in response.json()["response"]:
            row["category"] = category
            row["currency_symbol"] = self.CURRENCY_SYMBOL
            yield Project.parse_obj(row).dict()


if __name__ == "__main__":
    start_crawl(KworkSpider)
