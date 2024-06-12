from enum import Enum
from typing import Optional

from aiogram.filters.callback_data import CallbackData


class Action(str, Enum):
    add = "add"
    get = "get"
    set = "set"
    start = "start"
    delete = "delete"


class Type(str, Enum):
    response = "response"
    analyze = "analyze"
    complain = "complain"
    answer = "answer"


class Complain(str, Enum):
    source = "source"
    category = "category"
    data = "data"
    response = "response"
    analyze = "analyze"
    other = "other"


class Token(CallbackData, prefix="token"):
    action: Action
    message_id: Optional[int] = None
    price: Optional[int] = None
    value: Optional[int] = None


class Subscribe(CallbackData, prefix="subscription"):
    action: Action
    message_id: Optional[int] = None
    tokens: Optional[int] = None
    value: Optional[int] = None


class Source(CallbackData, prefix="source"):
    action: Action
    code: Optional[str] = None


class Category(CallbackData, prefix="category"):
    action: Action
    code: Optional[str] = None


class Subcategory(CallbackData, prefix="subcategory"):
    action: Action
    code: Optional[str] = None


class Project(CallbackData, prefix="project"):
    id: int
    type: Type
    complain: Optional[Complain] = None


class GPTRequest(CallbackData, prefix="gpt"):
    id: Optional[int] = None
    type: Type
    action: Optional[Action] = None
    project_id: Optional[int] = None
    message_id: Optional[int] = None
    delete_message_id: Optional[str] = None
    complain: Optional[Complain] = None
