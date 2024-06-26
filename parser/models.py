import json
import uuid
from typing import Optional

from pydantic import BaseModel


class BaseProject(BaseModel):
    project_id: int
    price: Optional[int]
    title: str
    description: str
    source: str
    offers: int
    order_created: int
    url: str
    category: Optional[str]
    subcategory: Optional[str]
    currency_symbol: str
    price_max: Optional[int]


class BaseVacancy(BaseModel):
    vacancy_id: int
    title: str
    description: Optional[str]
    offers: int
    date_published: int
    salary_from: Optional[int]
    salary_to: Optional[int]
    currency_symbol: Optional[str]
    source: str
    url: str
    company: str
