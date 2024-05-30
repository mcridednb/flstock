import re
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlencode

import scrapy
from pydantic import Field, field_validator

from spiders.freelance.constants import CATEGORIES
from spiders.models import ExtraMixin
from spiders.utils import start_crawl


class Project(ExtraMixin):
    project_id: int
    price: Optional[int]
    title: str
    description: str
    source: str = Field(default="freelance")
    offers: int
    order_created: int
    url: str
    category: Optional[str] = None
    subcategory: Optional[str]
    currency_symbol: str
    price_max: Optional[int] = None

    @field_validator("offers", mode="before")
    def parse_offers(cls, value):
        if value:
            return int(re.sub(r"\D", "", value))

    @field_validator("order_created", mode="before")
    def parse_order_created(cls, value):
        if value:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z").timestamp()

    @field_validator("price", mode="before")
    def parse_price(cls, value):
        if value and "договорная" not in value.lower():
            return int(re.sub(r"\D", "", value))

    def get_id(self):
        return f"{self.source}_{self.project_id}"

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        data["_id"] = self.get_id()
        data["last_update"] = datetime.now()
        return data


class FreelanceSpider(scrapy.Spider):
    name = "freelance"
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "URLLENGTH_LIMIT": 100000,
    }
    CURRENCY_SYMBOL = "₽"
    BASE_URL = "https://freelance.ru/"
    PROJECTS_URL = urljoin(BASE_URL, "project/search/pro")

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate',
        'Accept': '*/*',
        'Connection': 'keep-alive'
    }

    def start_requests(self):
        for category in CATEGORIES:
            for subcategory in category["subcategories"]:
                params = {
                    "c": "",
                    "c[]": subcategory["id"],
                    "q": "",
                    "m": "or",
                    "e": "",
                    "a": [0, 1],
                    "v": [0, 1],
                    "f": "",
                    "t": "",
                    "o": [0, 1],
                    "b": "",
                    "b[]": [1, 2, 3]
                }
                encoded_params = urlencode(
                    [(k, v) for k, vals in params.items() for v in (vals if isinstance(vals, list) else [vals])]
                )
                url = f"{self.PROJECTS_URL}?{encoded_params}"
                yield scrapy.Request(
                    url=url,
                    method="GET",
                    callback=self.parse_projects,
                    headers=self.HEADERS,
                    meta={
                        "subcategory": subcategory["code"],
                    }
                )

    def parse_projects(self, response):
        subcategory = response.meta.get("subcategory")
        for project in response.css("div.projects .project"):
            title = " ".join([row.strip() for row in project.css("h2 a::text").extract()]).strip()
            project_id = project.css("a").attrib.get("href").split("/")[-1].rstrip(".html").split("-")[-1]
            url = urljoin(self.BASE_URL, project.css("a").attrib.get("href"))
            description = project.css(".description::text").get().strip()
            price = project.css(".cost::text").get().strip()

            try:
                offers = project.css(".comments-count::text").get().strip()
            except AttributeError:
                offers = '0'

            date = project.css(".timeago").attrib.get("datetime")

            yield Project.parse_obj({
                "project_id": project_id,
                "price": price,
                "title": title,
                "description": description,
                "offers": offers,
                "order_created": date,
                "url": url,
                "subcategory": subcategory,
                "currency_symbol": self.CURRENCY_SYMBOL,
            }).dict()


if __name__ == "__main__":
    start_crawl(FreelanceSpider)
