from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlencode

import scrapy
from pydantic import Field, field_validator

from spiders.kwork.constants import SUBCATEGORY_CATEGORY_MAP
from spiders.models import ExtraMixin
from spiders.utils import start_crawl


class Project(ExtraMixin):
    project_id: int = Field(alias="id")
    price: int
    title: str
    description: str
    source: str = Field(default="kwork")
    offers: int
    order_created: int = Field(alias="date_confirm")
    subcategory: int = Field(alias="category_id")
    category: Optional[int] = Field(alias="parent_category_id")
    price_max: Optional[int] = Field(alias="possible_price_limit")

    @field_validator("category", mode="before")
    def parse_category(cls, value):
        return SUBCATEGORY_CATEGORY_MAP[value] if not value else value

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

    def start_requests(self):
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

    def parse_token(self, response):
        self._token = response.json()["response"]["token"]

        query_string = urlencode({
            "categories": "all",
            "token": self._token,
        })
        url = f"{self.PROJECTS_URL}?{query_string}"
        yield scrapy.Request(
            url=url,
            method="POST",
            callback=self.parse_projects,
            headers=self.HEADERS,
        )

    def parse_projects(self, response):
        for row in response.json()["response"]:
            result = Project.parse_obj(row).dict()
            # if result["category"] in [11]:  # only for testing
            yield result


if __name__ == "__main__":
    start_crawl(KworkSpider)
