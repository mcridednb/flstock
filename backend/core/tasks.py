import io
import json
import random
from datetime import datetime, timedelta
from io import BytesIO

import html2text
import matplotlib.pyplot as plt
import pandas as pd
import pytz
import requests
import seaborn as sns
from django.conf import settings
from django.utils.timezone import now
from loguru import logger

from backend.celery import app
from core.models import Project, TelegramUser, Source, GPTPrompt, Category, Subcategory, GPTRequest, Vacancy
from core.utils import create_infographic


@app.task
def process_project_task(project):
    source = project.pop("source", None)
    if not source:
        logger.critical(f"Отсутствует источник: {project}")
        return

    try:
        source = Source.objects.get(
            code=source,
        )
    except Source.DoesNotExist:
        logger.critical(f"Неизвестный источник: {source}")
        return

    subcategory = project.pop("subcategory", None)
    if not subcategory:
        logger.critical(f"Отсутствует подкатегория: {subcategory}")
        return

    try:
        subcategory = Subcategory.objects.get(code=subcategory)
    except Exception as exc:
        logger.critical(f"Неизвестная подкатегория: {subcategory}")
        return

    category = project.pop("category", None)
    if not category:
        category = subcategory.category.code

    try:
        category = Category.objects.get(code=category)
    except Exception as exc:
        logger.critical(f"Неизвестная категория: {category}")
        return

    project, created = Project.objects.get_or_create(
        project_id=project["project_id"],
        source=source,
        defaults={
            "title": project.get("title"),
            "description": project.get("description"),
            "price": project.get("price"),
            "price_max": project.get("price_max"),
            "url": project.get("url"),
            "offers": project.get("offers"),
            "order_created": project.get("order_created"),
            "category": category,
            "subcategory": subcategory,
            "currency_symbol": project.get("currency_symbol"),
        },
    )
    if created:
        send_project_task.delay(project.id)


@app.task
def process_vacancy_task(vacancy):
    vacancy, created = Vacancy.objects.get_or_create(
        vacancy_id=vacancy["vacancy_id"],
        defaults={
            "title": vacancy.get("title"),
            "salary_from": vacancy.get("salary_from"),
            "salary_to": vacancy.get("salary_to"),
            "url": vacancy.get("url"),
            "offers": vacancy.get("offers"),
            "date_published": vacancy.get("date_published"),
            "currency_symbol": vacancy.get("currency_symbol"),
            "company": vacancy.get("company"),
        },
    )
    if created:
        date_published = datetime.fromtimestamp(vacancy.date_published, pytz.UTC)
        time_diff = now() - date_published
        minutes_ago = int(time_diff.total_seconds() / 60)

        salary_text = "Не указана"
        if vacancy.salary_from:
            salary_text = ""
            if vacancy.salary_from and vacancy.salary_to:
                salary_text = f"от {int(vacancy.salary_from)} до {int(vacancy.salary_to)} "
            elif vacancy.salary_from:
                salary_text = f"{int(vacancy.salary_from)} "
            elif vacancy.salary_to:
                salary_text = f"{int(vacancy.salary_to)} "

            salary_text += vacancy.currency_symbol

        keyboard = {
            "inline_keyboard": [
                [{"text": "🌐 Перейти к вакансии", "url": vacancy.url}],
            ]
        }
        token = "7487037085:AAHJGfWbbEiHAnxOAk8Z6jIm9BL5h_bw0-k"
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        img_data = create_infographic(
            vacancy.title,
            salary_text,
            vacancy.company,
            vacancy.offers,
            minutes_ago,
            "Python",
        )
        response = requests.post(
            url,
            data={
                "chat_id": 763797678,
                "reply_markup": json.dumps(keyboard),
            },
            files={
                "photo": BytesIO(img_data)
            }
        )


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
    caption = (
        f"{caption}\n\n"
        f'<a href="https://t.me/freelancerai_info">Новости проекта</a> | <a href="https://t.me/freelancerai_catalog">Каталог каналов</a>'
    )

    payload = {
        "chat_id": chat_id,
        "caption": caption,
        "reply_markup": json.dumps(keyboard),
        "photo": file_id,
        "parse_mode": "HTML",
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


def get_statistics_projects(last_update):
    category_data = []
    sources = Source.objects.all()
    for category in Category.objects.all().prefetch_related("subcategory_set"):
        subcategory_data = []
        for subcategory in category.subcategory_set.all():
            source_data = []
            for source in sources:
                source_data.append({
                    "title": source.title,
                    "count": Project.objects.filter(
                        source=source,
                        subcategory=subcategory,
                        order_created__gte=last_update
                    ).count()}
                )
            subcategory_data.append({"title": subcategory.title, "source_data": source_data})
        if subcategory_data:
            category_data.append({"title": category.title, "subcategory_data": subcategory_data})
    return category_data


def create_heatmap(category_data):
    # Сбор данных для DataFrame
    records = []
    for subcategory in category_data['subcategory_data']:
        for source in subcategory['source_data']:
            records.append({
                "subcategory": subcategory['title'],
                "source": source['title'],
                "count": source['count']
            })

    df = pd.DataFrame(records)
    pivot_df = df.pivot_table(index='subcategory', columns='source', values='count', fill_value=0)

    plt.figure(figsize=(12, 10))
    ax = sns.heatmap(
        pivot_df,
        vmin=0,
        vmax=10,
        annot=True,
        fmt="g",
        cmap="RdYlGn", linewidths=.5,
        annot_kws={"size": 14}, cbar_kws={'label': 'Количество заказов'},
    )

    ax.set_title(category_data['title'], fontsize=20)
    ax.set_xlabel('Площадки', fontsize=18)
    ax.set_ylabel('Подкатегории', fontsize=14)
    ax.tick_params(axis='x', labelsize=14, rotation=45)
    ax.tick_params(axis='y', labelsize=14, rotation=0)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf


def send_media_group(chat_id, images, caption=None, reply_to_message_id=None):
    token = settings.TELEGRAM_BOT_TOKEN

    SEND_MEDIA_GROUP = f'https://api.telegram.org/bot{token}/sendMediaGroup'

    files = {}
    media = []
    for i, buf in enumerate(images):
        name = f'photo{i}'
        files[name] = buf.read()
        buf.close()
        # a list of InputMediaPhoto. attach refers to the name of the file in the files dict
        media.append(dict(type='photo', media=f'attach://{name}'))
    if caption:
        media[0]['caption'] = caption
    return requests.post(SEND_MEDIA_GROUP, data={
        'chat_id': chat_id,
        'message_thread_id': 21,
        'media': json.dumps(media),
        'reply_to_message_id': reply_to_message_id,
    }, files=files)


@app.task(name="send_statistic_project")
def send_statistic_project():
    last_update = datetime.today() - timedelta(days=7)
    statistics = get_statistics_projects(int(last_update.timestamp()))
    images = [create_heatmap(category_data) for category_data in statistics]
    send_media_group("-1002238232891", images)
