import json
import uuid
from typing import Optional

from pydantic import BaseModel


class BaseProject(BaseModel):
    project_id: int
    price: int
    title: str
    description: str
    source: str
    offers: int
    order_created: int
    subcategory: int
    url: str
    category: Optional[int]
    price_max: Optional[int]

    def to_celery(self, task):
        task_data = {
            "id": str(uuid.uuid4()),
            "task": task,
            "args": [self.dict()],
            "kwargs": {},
        }
        return json.dumps(task_data)
