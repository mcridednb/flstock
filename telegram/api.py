import logging
import os
from urllib.parse import urljoin

from aiohttp import ClientSession
from aiohttp import hdrs
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")
API_URL = urljoin(BACKEND_URL, "/api/")


async def api_call(method, endpoint, params=None, json=None):
    try:
        async with ClientSession() as session:
            headers = {"Content-Type": "application/json"}
            url = urljoin(API_URL, endpoint)
            response = await session.request(method, url, json=json, params=params, headers=headers)
            return await response.json(), response.status
    except Exception as exc:
        logger.exception(exc)
        logger.info(response.text())

async def user_create(message, referrer):
    endpoint = "telegram-users/"
    data = {
        "chat_id": message.from_user.id,
        "username": message.from_user.username,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
        "referrer": referrer,
    }
    return await api_call(hdrs.METH_POST, endpoint, json=data)


async def registration_success(message):
    endpoint = urljoin("telegram-users/", str(message.from_user.id) + "/")
    endpoint = urljoin(endpoint, "registration-success")
    data = {
        "chat_id": message.from_user.id,
    }
    return await api_call(hdrs.METH_POST, endpoint, json=data)


async def user_detail(chat_id):
    endpoint = urljoin("telegram-users/", str(chat_id))
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


async def subcategories_list(chat_id, category_code):
    endpoint = "subcategories/"
    params = {
        "category": category_code,
        "chat_id": chat_id,
    }
    return await api_call(hdrs.METH_GET, endpoint, params=params)


async def category_subscribe(chat_id, subcategory_code):
    endpoint = "category-subscribe"
    data = {
        "chat_id": chat_id,
        "subcategory_code": subcategory_code,
    }
    return await api_call(hdrs.METH_POST, endpoint, json=data)


async def projects_list():
    endpoint = "projects/"
    return await api_call(hdrs.METH_GET, endpoint)


async def projects_detail(project_id):
    endpoint = urljoin("projects/", str(project_id))
    return await api_call(hdrs.METH_GET, endpoint)


async def gpt_request_create(
    project_id, chat_id, message_id, delete_message_id, request_type, additional_info=None
):
    endpoint = urljoin("projects/", str(project_id) + "/")
    endpoint = urljoin(endpoint, "gpt")
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "delete_message_id": delete_message_id,
        "request_type": request_type,
        "additional_info": additional_info,
    }
    return await api_call(hdrs.METH_POST, endpoint, json=data)


async def sources_list(message):
    endpoint = "sources/"
    params = {
        "chat_id": message.from_user.id,
    }
    return await api_call(hdrs.METH_GET, endpoint, params=params)


async def source_subscribe(chat_id, source_code):
    endpoint = "source-subscribe"
    data = {
        "chat_id": chat_id,
        "source_code": source_code,
    }
    return await api_call(hdrs.METH_POST, endpoint, json=data)


async def create_payment(chat_id, tokens, value, delete_message_id):
    endpoint = "payment"
    data = {
        "user": chat_id,
        "tokens": tokens,
        "value": value,
        "delete_message_id": delete_message_id,
    }
    return await api_call(hdrs.METH_POST, endpoint, json=data)


async def add_subscription(chat_id, tokens, value, delete_message_id):
    endpoint = "add-subscription"
    data = {
        "user": chat_id,
        "tokens": tokens,
        "value": value,
        "type": "subscription",
        "delete_message_id": delete_message_id,
    }
    return await api_call(hdrs.METH_POST, endpoint, json=data)
