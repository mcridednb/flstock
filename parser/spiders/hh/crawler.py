import os
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

import redis
import scrapy
from dotenv import load_dotenv
from pydantic import Field, field_validator
from w3lib.http import basic_auth_header

from spiders.models import ExtraMixin
from spiders.utils import start_crawl

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)


class Vacancy(ExtraMixin):
    vacancy_id: int = Field(alias="vacancyId")
    title: str = Field(alias="name")
    description: Optional[str] = None
    offers: int = Field(alias="responsesCount")
    date_published: int = Field(alias="publicationTime")
    salary_from: Optional[int] = Field(alias="compensation")
    salary_to: Optional[int] = Field(alias="compensation")
    company: Optional[str] = Field(alias="company")
    currency_symbol: Optional[str] = None
    source: str = Field(default="hh")

    url: str = Field(alias="links")

    @field_validator("url", mode="before")
    def parse_url(cls, value):
        if value:
            return value["desktop"]

    @field_validator("company", mode="before")
    def parse_company(cls, value):
        if value:
            return value["name"]

    @field_validator("date_published", mode="before")
    def parse_date_published(cls, value):
        if value:
            return value["@timestamp"]

    @field_validator("salary_from", mode="before")
    def parse_salary_from(cls, value):
        if value:
            return value.get("from")

    @field_validator("salary_to", mode="before")
    def parse_salary_to(cls, value):
        if value:
            return value.get("to")

    def get_id(self):
        return f"{self.source}_{self.vacancy_id}"

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        data["_id"] = self.get_id()
        data["last_update"] = datetime.now()
        return data


class HHSpider(scrapy.Spider):
    name = "hh"
    allowed_domains = ["hh.ru"]
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 1,
        "URLLENGTH_LIMIT": 100000,
    }
    CURRENCY_SYMBOL = "₽"
    BASE_URL = "https://hh.ru/search/vacancy"

    HEADERS = {
        "Origin": "https://hh.ru",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Referer": "https://hh.ru/",
    }

    def __init__(self, keyword, *args, **kwargs):
        super().__init__()
        self.keyword = keyword
        self.login = "daperepechin"
        self.password = "WQS3WAZvWc"
        self.proxy = "http://78.46.100.233:43819"
        self.proxy_auth = basic_auth_header(self.login, self.password)

    def start_requests(self):
        yield scrapy.Request(
            url="https://hh.ru/",
            method="GET",
            callback=self.start_parsing,
            headers={
                **self.HEADERS,
                "Proxy-Authorization": self.proxy_auth,
            },
            meta={
                "proxy": self.proxy,
                "ssl_certificate_validation": False,
            }
        )

    def start_parsing(self, response):
        build = response.text.split("build: \"")[1].split("\"", 1)[0]
        query_string = urlencode({
            "text": self.keyword,
            "from": "suggest_post",
            "salary": "",
            "ored_clusters": "true",
            "order_by": "publication_time",
            "search_field": "name",
            "excluded_text": "",
            "page": "0",
            "disableBrowserCache": "true"
        })
        url = f"{self.BASE_URL}?{query_string}"
        yield scrapy.Request(
            url=url,
            method="GET",
            callback=self.parse_vacancies,
            headers={
                "Accept": "application/json",
                **self.HEADERS,
                "x-static-version": build,
                "Proxy-Authorization": self.proxy_auth,
            },
            meta={
                "proxy": self.proxy,
                "ssl_certificate_validation": False,
            }
        )

    def parse_vacancies(self, response):
        for vacancy in response.json()["vacancySearchResult"]["vacancies"]:
            vacancy["currency_symbol"] = vacancy.get("compensation", {}).get("currencyCode")
            try:
                result = Vacancy.parse_obj(vacancy).dict()
            except Exception as exc:
                pass
            yield result


if __name__ == "__main__":
    start_crawl(HHSpider, "python")
