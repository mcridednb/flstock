import time
from typing import Type

import requests
import scrapy
from loguru import logger
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def start_crawl(crawler: Type[scrapy.Spider], *args, **kwargs):
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(crawler, *args, **kwargs)
    process.start()


def reboot_mobile_proxy():
    logger.info("Rebooting proxy...")

    settings = get_project_settings()
    requests.get(settings.get("PROXY_REBOOT_URL"))
    time.sleep(30)
