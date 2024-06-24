import json
import random
from datetime import datetime
from io import BytesIO

import html2text
import pytz
import requests
from django.conf import settings
from django.utils.timezone import now
from loguru import logger

from backend.celery import app
from core.models import Project, TelegramUser, Source, GPTPrompt, Category, Subcategory, GPTRequest
from core.utils import create_infographic


@app.task
def process_order_task(order):
    source = order.pop("source", None)
    if not source:
        logger.critical(f"Отсутствует источник: {order}")
        return

    try:
        source = Source.objects.get(
            code=source,
        )
    except Source.DoesNotExist:
        logger.critical(f"Неизвестный источник: {source}")
        return

    subcategory = order.pop("subcategory", None)
    if not subcategory:
        logger.critical(f"Отсутствует подкатегория: {subcategory}")
        return

    try:
        subcategory = Subcategory.objects.get(code=subcategory)
    except Exception as exc:
        logger.critical(f"Неизвестная подкатегория: {subcategory}")
        return

    category = order.pop("category", None)
    if not category:
        category = subcategory.category.code

    try:
        category = Category.objects.get(code=category)
    except Exception as exc:
        logger.critical(f"Неизвестная категория: {category}")
        return

    project, created = Project.objects.get_or_create(
        project_id=order["project_id"],
        source=source,
        defaults={
            "title": order.get("title"),
            "description": order.get("description"),
            "price": order.get("price"),
            "price_max": order.get("price_max"),
            "url": order.get("url"),
            "offers": order.get("offers"),
            "order_created": order.get("order_created"),
            "category": category,
            "subcategory": subcategory,
            "currency_symbol": order.get("currency_symbol"),
        },
    )
    if created:
        send_project_task.delay(project.id)


def check_words(words, title, description):
    if not words:
        return False

    words = [word.strip().lower() for word in words.split(",")]
    for word in words:
        if word in title.lower() or word in description.lower():
            return True

    return False


@app.task
def send_user_task(chat_id, caption, keyboard, file_id, url):
    payload = {
        "chat_id": chat_id,
        "caption": caption,
        "reply_markup": json.dumps(keyboard),
        "photo": file_id,
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        print(f"Failed to send message to {chat_id}: {response.text}")


@app.task
def send_channel_task(chat_id, caption, file_id, url, project_url):
    if not random.choice([True, False, False]):
        return

    keyboard = json.dumps({
        "inline_keyboard": [
            [{"text": "🌐 Перейти к заказу", "url": project_url}],
            [{"text": "⚡ Больше заказов", "url": f"https://t.me/freelancerai_bot"}],
        ]
    })
    caption = (
        f"{caption}\n\n"
        f'<a href="https://t.me/freelancerai_info">Новости проекта</a> | <a href="https://t.me/freelancerai_catalog">Каталог каналов</a>\n\n'
        f'<a href="https://t.me/freelancerai_it">Подпишись</a>'
    )
    payload = {
        "chat_id": chat_id,
        "caption": caption,
        "reply_markup": keyboard,
        "photo": file_id,
        "parse_mode": "HTML",
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        print(f"Failed to send message to {chat_id}: {response.text}")


@app.task(name="send_project_task")
def send_project_task(project_id):
    project = Project.objects.get(id=project_id)
    if project.status == Project.StatusChoices.DISTRIBUTED:
        return

    order_created_datetime = datetime.fromtimestamp(project.order_created, pytz.UTC)
    time_diff = now() - order_created_datetime
    minutes_ago = int(time_diff.total_seconds() / 60)

    if minutes_ago > 600:
        return

    title = html2text.html2text(project.title).strip()
    title = title.split()
    title = f"{title[0].capitalize()} {' '.join(title[1:])}"
    description = html2text.html2text(project.description).strip()

    price_text = "Не указана"
    if project.price:
        price_text = ""
        if project.price and project.price_max:
            price_text = f"от {int(project.price)} до {int(project.price_max)} "
        elif project.price:
            price_text = f"{int(project.price)} "
        elif project.price_max:
            price_text = f"{int(project.price_max)} "

        price_text += project.currency_symbol

    users = TelegramUser.objects.filter(
        category_subscriptions__subcategory=project.subcategory,
        source_subscriptions__source=project.source,
    ).distinct()

    keyboard = {
        "inline_keyboard": [
            [{"text": "🌐 Перейти к заказу", "url": project.url}],
            [{"text": "🤖️ Составить отклик (1 токен)", "callback_data": f"project:{project.id}:response:"}],
            [{"text": "🚀 Составить отчёт (2 токена)", "callback_data": f"project:{project.id}:analyze:"}],
            [{"text": "⚠️ Сообщить об ошибке", "callback_data": f"project:{project.id}:complain:"}],
            [{"text": "❌ Закрыть", "callback_data": "close"}]
        ]
    }

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendPhoto"
    img_data = create_infographic(
        title,
        price_text,
        project.source.title,
        project.offers,
        minutes_ago,
        project.subcategory.title,
    )
    response = requests.post(
        url,
        data={
            "chat_id": -1002238232891,
            "message_thread_id": 2,
        },
        files={
            "photo": BytesIO(img_data)
        }
    )

    if len(description) > 350:
        caption = f"{description[:350]}...."
    else:
        caption = description

    file_id = response.json()["result"]["photo"][-1]["file_id"]

    for user in users:
        if user.min_price and project.price:
            if int(project.price) < user.min_price:
                if not project.price_max:
                    continue
                if int(project.price_max) < user.min_price:
                    continue

        if user.stop_words and user.stop_words.strip():
            has_stop_word = check_words(user.stop_words.strip(), title, description)
            if has_stop_word:
                continue

        if user.keywords and user.keywords.strip():
            has_keyword = check_words(user.keywords.strip(), title, description)
            if not has_keyword:
                continue

        send_user_task.delay(user.chat_id, caption, keyboard, file_id, url)

    if project.subcategory.category.telegram_group_id:
        send_channel_task.delay(
            project.subcategory.category.telegram_group_id, caption, file_id, url, project.url
        )

    project.status = Project.StatusChoices.DISTRIBUTED
    project.save()


def send_limit_exceeded_message(chat_id, delete_message_id):
    keyboard = json.dumps({
        "inline_keyboard": [[{
            "text": "🪙 Пополнить токены",
            "callback_data": f"token:get:::"
        }]]
    })

    data = {
        'chat_id': chat_id,
        'message_id': delete_message_id,
        'text': (
            "🚫 *Недостаточно токенов.*\n\n"
            "Нажмите на кнопку ниже, чтобы пополнить баланс."
        ),
        'parse_mode': 'Markdown',
        'reply_markup': keyboard
    }
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/editMessageText"
    response = requests.post(url, json=data)
    return response.json()


def send_edit_keyboard_message(chat_id, request_id, delete_message_id):
    keyboard = json.dumps({
        "inline_keyboard": [[{
            "text": "⚠️ Сообщить об ошибке",
            "callback_data": f"gpt:{request_id}:complain:::::"
        }]]
    })

    data = {
        'chat_id': chat_id,
        'message_id': delete_message_id,
        'parse_mode': 'Markdown',
        'reply_markup': keyboard,
    }
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/editMessageReplyMarkup"
    response = requests.post(url, json=data)
    return response.json()


@app.task(name="gpt_request")
def gpt_request(project_id, message_id, delete_message_id, chat_id, request_type, additional_info):
    try:
        user = TelegramUser.objects.get(chat_id=chat_id)
    except TelegramUser.DoesNotExist as exc:
        return

    if user.tokens <= 0:
        send_limit_exceeded_message(user.chat_id, delete_message_id)
        return

    project = Project.objects.get(id=project_id)
    prompt = GPTPrompt.objects.get(
        model__code="gpt-4o",
        type=request_type,
        category=project.category,
    )
    request = GPTRequest.objects.create(
        prompt=prompt,
        user=user,
        project=project,
        type=request_type,
        additional_info=additional_info,
    )
    send_edit_keyboard_message(chat_id, request.id, delete_message_id)
    request.send_user_response(message_id, delete_message_id)
