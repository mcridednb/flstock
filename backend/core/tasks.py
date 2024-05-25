import json
from datetime import datetime
from io import BytesIO

import html2text
import pytz
import redis
import requests
from django.conf import settings
from django.utils.timezone import now
from loguru import logger
from openai import OpenAI

from backend.celery import app
from core.models import Project, CategorySubscription, TelegramUser, Source, GPTPrompt, Category, Subcategory
from core.utils import send_limit_exceeded_message, send_html_to_telegram, create_infographic


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

    category = order.pop("category", None)
    if not category:
        logger.critical(f"Отсутствует категория: {category}")
        return

    try:
        category = Category.objects.get(code=category)
    except Exception as exc:
        logger.critical(f"Неизвестная категория: {category}")
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
        price_text = f"от {int(project.price)} до {int(project.price_max)} "
    elif project.price:
        price_text = f"{int(project.price)} "
    elif project.price_max:
        price_text = f"{int(project.price_max)} "

    price_text += project.currency_symbol

    gpt_prompt = GPTPrompt.objects.filter(
        category=project.category,
    )

    users = TelegramUser.objects.filter(subscriptions__subcategory=project.subcategory).distinct()

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
        stop = False
        stop_words = [word.strip().lower() for word in user.stop_words.split(",")]
        for stop_word in stop_words:
            if stop_word in title.lower() or stop_word in description.lower():
                stop = True

        if stop:
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
    ) + "\n" + str(prompt.json_format)

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
