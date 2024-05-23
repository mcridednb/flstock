import io
import json
from datetime import datetime

import html2text
import pdfkit
import pytz
import redis
import requests
from django.conf import settings
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils.timezone import now
from loguru import logger
from openai import OpenAI

from backend.celery import app
from core.models import Project, CategorySubscription, TelegramUser, Source, GPTPrompt


def create_pdf_file(response, template_name):
    html_content = render_to_string(template_name, {'response': response})
    options = {
        'encoding': 'UTF-8'
    }
    pdf_buffer = pdfkit.from_string(html_content, False, options=options)
    buffer = io.BytesIO(pdf_buffer)
    buffer.seek(0)
    return buffer


def send_html_to_telegram(chat_id, message_id, response, template_name):
    pdf_buffer = create_pdf_file(response, template_name)
    files = {
        'document': (f'report.pdf', pdf_buffer, 'application/pdf')
    }
    data = {
        'chat_id': chat_id,
        'text': response["response"],
        'parse_mode': 'Markdown',
        'reply_to_message_id': message_id,
    }
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendDocument"
    response = requests.post(url, data=data, files=files)
    return response.json()


def send_limit_exceeded_message(chat_id, message_id, is_pro: bool):
    text = (
        "🚫 Дневной лимит на анализ данного типа превышен.\n"
        "Лимиты сбрасываются каждый день в 00:00 по МСК."
    )
    # keyboard = []
    # if not is_pro:
    #     keyboard.append([
    #         {
    #             'text': '🛒 Купить подписку',
    #             'callback_data': 'get_subscribe'
    #         }
    #     ])
    # else:
    #     keyboard.append([
    #         {
    #             'text': 'ℹ️ Подробнее о лимитах',
    #             'callback_data': 'limit_info'
    #         }
    #     ])
    # keyboard = {
    #     'inline_keyboard': keyboard
    # }
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown',
        'reply_to_message_id': message_id,
        # 'reply_markup': keyboard
    }
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(url, json=data)
    return response.json()


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

    source_category = source.categories.get(code=str(order.get("category")))

    # if order["subcategory"]:
    #     subcategory = Subcategory.objects.get(id=order["subcategory"])
    # else:
    # subcategory = None
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
            "category": source_category.category,
        },
    )
    if created:
        send_project_task.delay(project.id)


@app.task(name="send_project_task")
def send_project_task(project_id):
    project = Project.objects.get(id=project_id)
    if project.status == Project.StatusChoices.DISTRIBUTED:
        return

    order_created_datetime = datetime.fromtimestamp(project.order_created, pytz.UTC)
    time_diff = now() - order_created_datetime
    minutes_ago = int(time_diff.total_seconds() / 60)

    title = html2text.html2text(project.title).strip()
    description = html2text.html2text(project.description).strip()

    price_text = ""
    if project.price and project.price_max:
        price_text = f"💰 *Цена*: от {project.price} до {project.price_max}\n\n"
    elif project.price:
        price_text = f"💰 *Цена*: {project.price}\n\n"
    elif project.price_max:
        price_text = f"💰 *Максимальная цена*: {project.price_max}\n\n"

    text = (
        f"📋 *Проект*: {title}\n\n"
        f"📝 *Описание*: {description}\n\n"
        f"{price_text}"
        f"🌐 *Источник*: {project.source.title}\n\n"
        f"💼 *Количество офферов*: {project.offers}\n\n"
        f"⏱️ *Создано*: {minutes_ago} минут назад{' ⚠️' if minutes_ago > 60 * 48 else ''}"
    )

    gpt_prompt = GPTPrompt.objects.filter(
        category=project.category,
    )

    chat_ids = CategorySubscription.objects.filter(
        Q(category=project.category) | Q(subcategory=project.subcategory)
    ).distinct().values_list('user__chat_id', flat=True)

    keyboard = {
        "inline_keyboard": [
            [{"text": "📋 Перейти к заказу", "url": project.url}],
        ]
    }
    if gpt_prompt:
        keyboard["inline_keyboard"].append(
            [{"text": "🤖 Проанализировать заказ (AI)", "callback_data": f"analyze_order_ai:{project.id}"}],
        )
    # if gpt_prompt.count() > 1:
    #     keyboard["inline_keyboard"].append(
    #         [{"text": "🧠 Проанализировать заказ (PRO AI)", "callback_data": f"analyze_order_pro_ai:{project.id}"}],
    #     )

    keyboard["inline_keyboard"].append([{"text": "❌ Не интересно", "callback_data": "close"}])
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    for chat_id in chat_ids:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "reply_markup": keyboard,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Failed to send message to {chat_id}: {response.text}")

    project.status = Project.StatusChoices.DISTRIBUTED
    project.save()


@app.task(name="gpt_request")
def gpt_request(project_id, message_id, chat_id, gpt_model_id):
    redis_client = redis.StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=1,
    )

    def get_gpt_model_count(chat_id, gpt_model_id):
        count = redis_client.hget(chat_id, gpt_model_id)
        return int(count) if count else 0

    project = Project.objects.get(id=project_id)

    try:
        user = TelegramUser.objects.get(chat_id=chat_id)
    except TelegramUser.DoesNotExist as exc:
        ...  # отправить сообщение что что-то пошло не так
        return

    limits = user.get_limits()
    if get_gpt_model_count(chat_id, gpt_model_id) >= limits[gpt_model_id]:
        send_limit_exceeded_message(chat_id, message_id, bool(user.user_subscription))
        return

    prompt = GPTPrompt.objects.get(
        model__code=gpt_model_id,
        category=project.category,
    )
    request = prompt.text.format(
        name=user.name,
        summary=user.summary,
        skills=user.skills,
        experience=user.experience,
        title=project.title,
        description=project.description,
        price=project.price,
        price_max=project.price_max,
    ) + prompt.json_format

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    messages = [
        {"role": "user", "content": request}
    ]

    completion = client.chat.completions.create(
        model=gpt_model_id,
        response_format={"type": "json_object"},
        messages=messages,
    )
    response_content = completion.choices[0].message.content
    response_json = json.loads(response_content)

    redis_client.hincrby(chat_id, gpt_model_id, 1)

    total_hours = sum(stage["time"] for stage in response_json["stages"])
    potential_price = total_hours * user.hourly_rate if user.hourly_rate else None

    template_name = f"{project.category.code}_report.html"
    response_json["hourly_rate"] = user.hourly_rate
    response_json["project_title"] = html2text.html2text(project.title).strip()
    response_json["project_description"] = html2text.html2text(project.description).strip()
    response_json["total_hours"] = total_hours
    response_json["potential_price"] = potential_price
    send_html_to_telegram(user.chat_id, message_id, response_json, template_name)


# celery -A backend worker --loglevel=info
# celery -A backend beat --loglevel=info
@app.task(name="clean_gpt_limits")
def clean_gpt_limits():
    redis_client = redis.StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=1,
    )
    redis_client.flushdb()
