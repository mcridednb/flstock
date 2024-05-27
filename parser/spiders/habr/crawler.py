import re
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlencode

import pytz
import scrapy
from pydantic import Field, field_validator

from spiders.habr.constants import CATEGORIES
from spiders.models import ExtraMixin
from spiders.utils import start_crawl


class Project(ExtraMixin):
    project_id: int
    price: Optional[int]
    title: str
    description: str
    source: str = Field(default="habr")
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
        months = {
            'января': 'January',
            'февраля': 'February',
            'марта': 'March',
            'апреля': 'April',
            'мая': 'May',
            'июня': 'June',
            'июля': 'July',
            'августа': 'August',
            'сентября': 'September',
            'октября': 'October',
            'ноября': 'November',
            'декабря': 'December',
        }
        if value:
            parts = value.split()
            parts[1] = months[parts[1]]
            new_date_str = ' '.join(parts)
            dt = datetime.strptime(new_date_str, "%d %B %Y, %H:%M")
            moscow_tz = pytz.timezone('Europe/Moscow')
            localized_dt = moscow_tz.localize(dt)
            return localized_dt.timestamp()

    @field_validator("price", mode="before")
    def parse_price(cls, value):
        if value and "договорная" not in value:
            return int(re.sub(r"\D", "", value))

    def get_id(self):
        return f"{self.source}_{self.project_id}"

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        data["_id"] = self.get_id()
        data["last_update"] = datetime.now()
        return data


class HabrSpider(scrapy.Spider):
    name = "habr"
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "URLLENGTH_LIMIT": 100000,
    }
    CURRENCY_SYMBOL = "₽"
    BASE_URL = "https://freelance.habr.com/"
    PROJECTS_URL = urljoin(BASE_URL, "tasks")

    HEADERS = {
        "User-Agent": "android",
        "Accept-Encoding": "gzip, deflate, br",
        "Host": "freelance.habr.com",
        "Connection": "keep-alive",
    }

    def start_requests(self):
        for category in CATEGORIES:
            for subcategory in category["subcategories"]:
                params = {
                    "categories": subcategory["id"],
                }
                url = f"{self.PROJECTS_URL}?{urlencode(params)}"
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
        for url in response.css("#tasks_list .task__title a")[:5]:
            url = urljoin(self.BASE_URL, url.attrib.get("href"))
            yield scrapy.Request(
                url=url,
                method="GET",
                callback=self.parse_project,
                headers=self.HEADERS,
                meta=response.meta,
            )

    def parse_project(self, response):
        subcategory = response.meta.get("subcategory")
        if "Заказ в архиве" in response.text:
            return
        title = " ".join([line.strip() for line in response.css("h2 *::text").extract()]).strip()
        price = " ".join([line.strip() for line in response.css(".task__finance *::text").extract()]).strip()
        date, offers, views = " ".join([
            line.strip() for line in response.css(".task__meta *::text").extract()
        ]).strip().split("\n •")
        description = " ".join([line.strip() for line in response.css(".task__description *::text").extract()]).strip()
        project_id = response.url.split("/")[-1]
        order = Project.parse_obj({
            "project_id": project_id,
            "price": price,
            "title": title,
            "description": description,
            "offers": offers,
            "order_created": date,
            "url": response.url,
            "subcategory": subcategory,
            "currency_symbol": self.CURRENCY_SYMBOL,
        }).dict()
        yield order


if __name__ == "__main__":
    start_crawl(HabrSpider)
