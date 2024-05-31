import hashlib
import hmac
import logging
import os
from urllib.parse import urljoin

from aiohttp import ClientSession
from aiohttp import hdrs
from asgiref.sync import async_to_sync
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


async def projects_analyze(
    project_id, chat_id, message_id, delete_message_id, additional_info=None
):
    endpoint = urljoin("projects/", str(project_id) + "/")
    endpoint = urljoin(endpoint, "analyze")
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "delete_message_id": delete_message_id,
    }
    return await api_call(hdrs.METH_POST, endpoint, json=data)


async def sources_list(message):
    endpoint = "sources/"
    params = {
        "chat_id": message.from_user.id,
    }
    return await api_call(hdrs.METH_GET, endpoint, params=params)


async def source_subscribe(message):
    endpoint = "source-subscribe"
    data = {
        "chat_id": message.from_user.id,
        "source_code": message.data,
    }
    return await api_call(hdrs.METH_POST, endpoint, json=data)


def calculate_signature(currency, amount, header, description, api_key):
    message = f"{currency}{amount}{header}{description}".encode('utf-8')
    secret = api_key.encode('utf-8')
    signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
    return signature


# @async_to_sync
# print(bitbanker_create_bill("2000", "Николай", 7658262, "requests", 10))
async def bitbanker_create_bill(amount: int, name: str, chat_id, payment_type, count):
    url = "https://api.aws.bitbanker.org/latest/api/v1/invoices"
    currency = "RUB.R"
    header = "Фрилансер"
    description = "Доступ к услугам @freelancerai_bot"
    api_key = os.getenv("BITBANKER_API_KEY")
    data = {
        "payment_currencies": [
            "BTC",
            "USDT",
            "TRX",
        ],
        "currency": currency,  # валюта счета, возможные значения: BTC, ETH, USDT, USDC, TRX, ATOM, AVAX, RUB.R
        "amount": amount,
        "description": description,
        "language": "ru",
        "header": header,
        "payer": name,
        "is_convert_payments": False,
        "data": {
            "chat_id": chat_id,
            "payment_type": payment_type,
            "count": count,
        },
        "sign": calculate_signature(currency, amount, header, description, api_key),
    }
    async with ClientSession() as session:
        headers = {
            "X-API-KEY": api_key
        }
        response = await session.request("POST", url, json=data, headers=headers)
        json_response = await response.json()

        if 199 < response.status < 300:
            return json_response["link"]
