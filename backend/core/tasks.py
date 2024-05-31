import json
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


@app.task(name="send_project_task")
def send_project_task(project_id):
    project = Project.objects.get(id=project_id)
    if project.status == Project.StatusChoices.DISTRIBUTED:
        return

    order_created_datetime = datetime.fromtimestamp(project.order_created, pytz.UTC)
    time_diff = now() - order_created_datetime
    minutes_ago = int(time_diff.total_seconds() / 60)

    if minutes_ago > 120:
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

    gpt_prompt = GPTPrompt.objects.filter(
        category=project.category,
    )

    users = TelegramUser.objects.filter(
        category_subscriptions__subcategory=project.subcategory,
        source_subscriptions__source=project.source,
    ).distinct()

    keyboard = {
        "inline_keyboard": [
            [{"text": "📋 Перейти к заказу", "url": project.url}],
        ]
    }

    if gpt_prompt:
        keyboard["inline_keyboard"].append(
            [{"text": "🤖 Проанализировать заказ (AI)", "callback_data": f"analyze_order_pro_ai:{project.id}"}],
        )

    keyboard["inline_keyboard"].append([{"text": "❌ Не интересно", "callback_data": "close"}])
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendPhoto"
    img_data = create_infographic(
        title,
        price_text,
        project.source.title,
        project.offers,
        minutes_ago,
        project.subcategory.title,
    )

    for user in users:
        if user.stop_words and user.stop_words.strip():
            has_stop_word = check_words(user.stop_words.strip(), title, description)
            if has_stop_word:
                continue

        if user.keywords and user.keywords.strip():
            has_keyword = check_words(user.keywords.strip(), title, description)
            if not has_keyword:
                continue

        if len(description) > 350:
            caption = f"{description[:350]}...."
        else:
            caption = description

        payload = {
            "chat_id": user.chat_id,
            "caption": caption,
            "reply_markup": json.dumps(keyboard),
        }
        response = requests.post(url, data=payload, files={
            "photo": BytesIO(img_data)
        })
        if response.status_code != 200:
            print(f"Failed to send message to {user.chat_id}: {response.text}")
            return

    project.status = Project.StatusChoices.DISTRIBUTED
    project.save()


def send_limit_exceeded_message(chat_id, message_id, delete_message_id):
    keyboard = json.dumps({
        "inline_keyboard": [[{
            "text": "🤖 Купить AI-запросы",
            "callback_data": f"buy_gpt_requests:{message_id}"
        }]]
    })

    data = {
        'chat_id': chat_id,
        'message_id': delete_message_id,
        'text': (
            "🚫 *Достигнут лимит запросов.*\n\n"
            "Нажмите на кнопку ниже, чтобы купить больше запросов."
        ),
        'parse_mode': 'Markdown',
        'reply_markup': keyboard
    }
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/editMessageText"
    response = requests.post(url, json=data)
    return response.json()


@app.task(name="gpt_request")
def gpt_request(project_id, message_id, delete_message_id, chat_id, additional_info):
    try:
        user = TelegramUser.objects.get(chat_id=chat_id)
    except TelegramUser.DoesNotExist as exc:
        ...  # отправить сообщение что что-то пошло не так
        return

    if user.gpt_request_limit <= 0:
        send_limit_exceeded_message(user.chat_id, message_id, delete_message_id)
        return

    project = Project.objects.get(id=project_id)
    prompt = GPTPrompt.objects.get(
        model__code="gpt-4o",
        category=project.category,
    )
    GPTRequest.objects.create(
        prompt=prompt,
        user=user,
        project=project,
        additional_info=additional_info,
    ).send_user_response(message_id, delete_message_id)

# celery -A backend worker --loglevel=info
# celery -A backend beat --loglevel=info
# @app.task(name="clean_gpt_limits")
# def clean_gpt_limits():
#     redis_client = redis.StrictRedis(
#         host=settings.REDIS_HOST,
#         port=settings.REDIS_PORT,
#         db=1,
#     )
#     redis_client.flushdb()
