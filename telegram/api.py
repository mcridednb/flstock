import logging
import os
from urllib.parse import urljoin

from aiohttp import ClientSession
from aiohttp import hdrs
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

BACKEND_URL = os.getenv("BACKEND_URL")
API_URL = urljoin(BACKEND_URL, "/api/")


async def api_call(method, endpoint, params=None, json=None):
    async with ClientSession() as session:
        headers = {"Content-Type": "application/json"}
        url = urljoin(API_URL, endpoint)
        response = await session.request(method, url, json=json, params=params, headers=headers)
        return await response.json(), response.status


async def user_create(message):
    endpoint = "telegram-users/"
    data = {
        "chat_id": message.from_user.id,
        "username": message.from_user.username,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name
    }
    return await api_call(hdrs.METH_POST, endpoint, json=data)


async def user_detail(message):
    endpoint = urljoin("telegram-users/", str(message.from_user.id))
    return await api_call(hdrs.METH_GET, endpoint)


async def user_patch(message, field, value):
    endpoint = urljoin("telegram-users/", str(message.from_user.id))
    data = {field: value}
    return await api_call(hdrs.METH_PATCH, endpoint, json=data)


async def categories_list(message):
    endpoint = "categories/"
    params = {
        "chat_id": message.from_user.id,
    }
    return await api_call(hdrs.METH_GET, endpoint, params=params)


async def subcategories_list(category, message):
    endpoint = "subcategories/"
    params = {
        "category": category,
        "chat_id": message.from_user.id,
    }
    return await api_call(hdrs.METH_GET, endpoint, params=params)


async def category_subscribe(message):
    endpoint = "category-subscribe"
    data = {
        "chat_id": message.from_user.id,
        "subcategory_code": message.data,
    }
    return await api_call(hdrs.METH_POST, endpoint, json=data)


async def projects_list():
    endpoint = "projects/"
    return await api_call(hdrs.METH_GET, endpoint)


async def projects_detail(project_id):
    endpoint = urljoin("projects/", str(project_id))
    return await api_call(hdrs.METH_GET, endpoint)


async def projects_analyze(project_id, chat_id, message_id, model):
    model_map = {
        "base": "gpt-3.5-turbo",
        "pro": "gpt-4o"
    }
    endpoint = urljoin("projects/", str(project_id) + "/")
    endpoint = urljoin(endpoint, "analyze")
    data = {
        "model": model_map[model],
        "chat_id": chat_id,
        "message_id": message_id,
    }
    return await api_call(hdrs.METH_POST, endpoint, json=data)
