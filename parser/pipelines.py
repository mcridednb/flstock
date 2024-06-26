from datetime import datetime
from typing import Optional

import pymongo
import pymongo.database
from celery import Celery
from scrapy import Spider

from models import BaseProject, BaseVacancy


class FlstockPipeline:
    def process_item(self, item, spider):
        return item


class MongoPipeline:
    mongo_db = "scraping"
    client: Optional[pymongo.MongoClient]
    collection_name: Optional[str]
    db: Optional[pymongo.database.Database]

    def __init__(self, mongo_uri):
        self.mongo_uri = mongo_uri

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.get("MONGO_URI"))

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.collection_name = spider.name

    def process_item(self, item: dict, spider: Spider):
        self.db[self.collection_name].update_one(
            {"_id": item["_id"]}, {
                "$set": item,
                "$setOnInsert": {"created_at": datetime.utcnow()}
            }, upsert=True
        )
        return item

    def close_spider(self, spider: Spider):
        self.client.close()


class CeleryPipeline:
    PROJECT_NAME = "backend"
    PROJECT_CELERY_TASK_NAME = "core.tasks.process_project_task"
    VACANCY_CELERY_TASK_NAME = "core.tasks.process_vacancy_task"

    def open_spider(self, spider):
        self.app = Celery(
            self.PROJECT_NAME,
            broker='pyamqp://{}:{}@{}:{}/'.format(
                spider.settings.get("RABBITMQ_USERNAME"),
                spider.settings.get("RABBITMQ_PASSWORD"),
                spider.settings.get("RABBITMQ_HOST"),
                spider.settings.get("RABBITMQ_PORT"),
            )
        )

    def close_spider(self, spider):
        self.app.close()

    def process_item(self, item, spider):
        task_name = self.PROJECT_CELERY_TASK_NAME
        try:
            message = BaseProject.parse_obj(item)
        except Exception as exc:
            message = BaseVacancy.parse_obj(item)
            task_name = self.VACANCY_CELERY_TASK_NAME

        self.app.send_task(
            task_name,
            args=[message.dict()]
        )

        return item
