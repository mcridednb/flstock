import os
import re
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv
from loguru import logger
from redis import asyncio as redis

import api
from states import Profile, Registration

load_dotenv()
logger.remove()
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS!UTC}</green> | "
    "<level>{level}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)
logger.add(sys.stdout, format=log_format)
logger.add(
    f"logs/bot.log",
    format=log_format,
    rotation="10 MB",
    compression="zip",
    enqueue=True,
)

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = 8888
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
BASE_WEBHOOK_URL = os.getenv("BASE_WEBHOOK_URL")

redis_client = redis.StrictRedis(host=REDIS_HOST, port=int(REDIS_PORT), db=3)
dp = Dispatcher(storage=RedisStorage(redis=redis_client))


async def get_subscriptions_keyboard(category, message):
    subcategories, _ = await api.subcategories_list(category, message)
    buttons = []
    for subcategory in subcategories:
        title = subcategory["title"]
        if subcategory["is_subscribed"]:
            title = f"✅{title}"
        buttons.append([types.InlineKeyboardButton(
            text=title,
            callback_data=f"{subcategory['code']}",
        )])

    buttons.append([types.InlineKeyboardButton(
        text="⬅️Назад",
        callback_data="back",
    )])

    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_categories_keyboard(message, state):
    categories, _ = await api.categories_list(message)
    buttons = []
    for category in categories:
        title = category["title"]
        if category["is_subscribed"]:
            title = f"✅{title}"
        buttons.append([types.InlineKeyboardButton(
            text=title,
            callback_data=f"{category['code']}",
        )])

    state = await state.get_state()
    if state in [Registration.category, Registration.subcategory]:
        buttons.append([types.InlineKeyboardButton(
            text="Далее ➡️",
            callback_data="next",
        )])
    else:
        buttons.append([types.InlineKeyboardButton(
            text="⬅️Назад",
            callback_data="back",
        )])

    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_sources_keyboard(message, state):
    sources, _ = await api.sources_list(message)
    buttons = []
    for source in sources:
        title = source["title"]
        if source["is_subscribed"]:
            title = f"✅{title}"
        buttons.append([types.InlineKeyboardButton(
            text=title,
            callback_data=f"{source['code']}",
        )])

    state = await state.get_state()
    if state in [Registration.source]:
        buttons.append([types.InlineKeyboardButton(
            text="Далее ➡️",
            callback_data="next",
        )])
    else:
        buttons.append([types.InlineKeyboardButton(
            text="⬅️Назад",
            callback_data="back",
        )])

    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_close_keyboard():
    buttons = [[types.InlineKeyboardButton(
        text="❌Закрыть",
        callback_data="close",
    )]]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_menu_keyboard(message_id):
    buttons = [[types.InlineKeyboardButton(
        text="👤 Редактировать профиль",
        callback_data="profile",
    )], [types.InlineKeyboardButton(
        text="🌐 Редактировать источники",
        callback_data="sources",
    )], [types.InlineKeyboardButton(
        text="📝 Редактировать категории",
        callback_data="categories",
    )],
        [types.InlineKeyboardButton(text="🤖 Купить AI-запросы", callback_data=f"buy_gpt_requests:{message_id}")],
        [types.InlineKeyboardButton(text="💳 Купить подписку", callback_data=f"buy_subscription:{message_id}")],
        [types.InlineKeyboardButton(
            text="❤️ Поддержать проект",
            callback_data="donate",
        )], [types.InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data="close",
        )]]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_change_profile_keyboard():
    buttons = [
        [types.InlineKeyboardButton(text="👤 Имя", callback_data="change_name")],
        [types.InlineKeyboardButton(text="🛠️ Навыки", callback_data="change_skills")],
        [types.InlineKeyboardButton(text="📝 О себе", callback_data="change_summary")],
        [types.InlineKeyboardButton(text="💼 Опыт", callback_data="change_experience")],
        [types.InlineKeyboardButton(text="⏰ Ставка в час", callback_data="change_hourly_rate")],
        [types.InlineKeyboardButton(text="🏷 Ключевые слова", callback_data="change_keywords")],
        [types.InlineKeyboardButton(text="⛔️ Минус слова", callback_data="change_stop_words")],
        [types.InlineKeyboardButton(text="❌ Закрыть", callback_data="close")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_buy_gpt_requests_keyboard():
    buttons = [
        [types.InlineKeyboardButton(text="10 запросов — 199₽", callback_data=f"buy_gpt_requests:10")],
        [types.InlineKeyboardButton(text="50 запросов + 1 PRO — 890₽", callback_data=f"buy_gpt_requests:50")],
        [types.InlineKeyboardButton(text="100 запросов + 3 PRO — 1580₽ ", callback_data=f"buy_gpt_requests:100")],
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_buy_subscription_keyboard():
    buttons = [
        [types.InlineKeyboardButton(text="1 месяц — 199₽", callback_data=f"buy_subscription:1")],
        [types.InlineKeyboardButton(text="3 месяца + 10 AI — 490₽", callback_data=f"buy_subscription:3")],
        [types.InlineKeyboardButton(text="6 месяцев + 30 AI — 890₽ ", callback_data=f"buy_subscription:6")],
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


async def on_startup(dispatcher: Dispatcher):
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET)


def check(member):
    return member.status != "left"


async def check_channels(user_id):
    buttons = []
    if not check(await bot.get_chat_member("-1002216378515", user_id)):
        buttons.append([types.InlineKeyboardButton(
            text="Новости нашего проекта", url="https://t.me/freelancerai_info"
        )])

    if buttons:
        me = await bot.get_me()
        buttons.append([types.InlineKeyboardButton(
            text="✅ Проверить", url=f"https://t.me/{me.username}?start="
        )])

        await bot.send_message(
            user_id,
            "Для работы с ботом нужно подписаться на:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        return

    return True


@dp.message(Command("start"))
async def send_welcome(message: Message, state: FSMContext):
    result = await check_channels(message.from_user.id)
    if not result:
        return

    response, _ = await api.user_create(message)
    if not response.get("username"):
        await state.clear()
        keyboard = await get_menu_keyboard(message.message_id)
        await message.answer(
            text="📋 *Выберите действие, которое хотите выполнить:*",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await state.set_state(Registration.source)
        keyboard = await get_sources_keyboard(message, state)
        await message.answer(
            "👋 *Добро пожаловать!*\n\n"
            "🔔 Пожалуйста, отметьте источники, "
            "по которым хотите получать уведомления:\n\n"
            "(Это можно будет изменить в настройках позднее)",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


@dp.callback_query(lambda call: call.data == "close")
async def process_close(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback_query.message.delete()


@dp.callback_query(lambda call: call.data == "check_subscription")
async def process_check_subscription(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    result = await check_channels(callback_query.from_user.id)
    if not result:
        return

    await send_welcome(callback_query.message, state)


@dp.callback_query(lambda call: call.data == "back")
async def process_back(callback_query: CallbackQuery, state: FSMContext) -> None:
    keyboard = await get_categories_keyboard(callback_query, state)

    if await state.get_state() == Registration.subcategory:
        await state.set_state(Registration.category)
        await callback_query.message.edit_text(
            "🔔 Теперь, пожалуйста, отметьте категории, "
            "по которым хотите получать уведомления:\n\n"
            "(Это всё ещё можно будет изменить в настройках позднее)",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    elif await state.get_state() == Profile.subcategory:
        await state.set_state(Profile.category)
        await callback_query.message.edit_text(
            "🔔 Пожалуйста, отметьте категории, "
            "по которым хотите получать уведомления:\n\n",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await state.clear()
        keyboard = await get_menu_keyboard(callback_query.message.message_id)
        await callback_query.message.edit_text(
            text="📋 *Выберите действие, которое хотите выполнить:*",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


@dp.message(Command("menu"))
async def process_menu(message: Message, state: FSMContext) -> None:
    result = await check_channels(message.from_user.id)
    if not result:
        return

    await state.clear()
    keyboard = await get_menu_keyboard(message.message_id)
    await message.answer(
        text="📋 *Выберите действие, которое хотите выполнить:*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: call.data == "next")
async def process_next(callback_query: CallbackQuery, state: FSMContext) -> None:
    if await state.get_state() in [Registration.category]:
        await state.clear()
        await callback_query.message.edit_text(
            "🎉 Отлично! Теперь вы будете получать уведомления.\n\n"
            "🔔 Вы всегда можете изменить свои предпочтения в настройках.\n\n"
            "Настройки бота: /menu\n"
            "Справка: /help",
            reply_markup=await get_close_keyboard()
        )
    else:
        await state.set_state(Registration.category)
        keyboard = await get_categories_keyboard(callback_query, state)
        await callback_query.message.edit_text(
            "🔔 Теперь, пожалуйста, отметьте категории, "
            "по которым хотите получать уведомления:\n\n"
            "(Это всё ещё можно будет изменить в настройках позднее)",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


@dp.callback_query(Registration.category)
async def process_category(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Registration.subcategory)
    await state.set_data({
        "category": callback_query.data
    })
    keyboard = await get_subscriptions_keyboard(callback_query.data, callback_query)
    await callback_query.message.edit_text(
        "🔔 Теперь, пожалуйста, отметьте категории, "
        "по которым хотите получать уведомления:\n\n"
        "(Это всё ещё можно будет изменить в настройках позднее)",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(Profile.category)
async def process_category(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Profile.subcategory)
    await state.set_data({
        "category": callback_query.data
    })
    keyboard = await get_subscriptions_keyboard(callback_query.data, callback_query)
    if len(keyboard.inline_keyboard) == 1:
        await callback_query.message.edit_text(
            "😔 К сожалению, выбранная категория сейчас недоступна.\nПожалуйста, выберите другую категорию.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await callback_query.message.edit_text(
            "🔔 Пожалуйста, отметьте категории, "
            "по которым хотите получать уведомления:\n\n",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


@dp.callback_query(Registration.subcategory)
async def process_subcategory(callback_query: CallbackQuery, state: FSMContext) -> None:
    response, status = await api.category_subscribe(callback_query)
    if status == 400:
        await callback_query.answer(response[0])
        return

    data = await state.get_data()
    keyboard = await get_subscriptions_keyboard(data["category"], callback_query)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


@dp.callback_query(Profile.subcategory)
async def process_subcategory(callback_query: CallbackQuery, state: FSMContext) -> None:
    response, status = await api.category_subscribe(callback_query)
    if status == 400:
        await callback_query.answer(response[0])
        return

    data = await state.get_data()
    keyboard = await get_subscriptions_keyboard(data["category"], callback_query)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


@dp.callback_query(Registration.source)
async def process_source(callback_query: CallbackQuery, state: FSMContext) -> None:
    response, status = await api.source_subscribe(callback_query)
    if status == 400:
        await callback_query.answer(response[0])
        return

    keyboard = await get_sources_keyboard(callback_query, state)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


@dp.callback_query(Profile.source)
async def process_source(callback_query: CallbackQuery, state: FSMContext) -> None:
    response, status = await api.source_subscribe(callback_query)
    if status == 400:
        await callback_query.answer(response[0])
        return

    keyboard = await get_sources_keyboard(callback_query, state)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


async def get_profile_data(message, state):
    profile, _ = await api.user_detail(message)
    await state.set_data(profile)
    profile_text = (
        f"👤 *Имя:* {profile['name'] or 'Не указано'}\n\n"
        f"🛠️ *Навыки:* {profile['skills'] or 'Не указано'}\n\n"
        f"📝 *О себе:* {profile['summary'] or 'Не указано'}\n\n"
        f"💼 *Опыт:* {profile['experience'] or 'Не указано'}\n\n"
        f"⏰ *Ставка в час:* {profile['hourly_rate'] or 'Не указано'}\n\n"
        f"🏷️ *Ключевые слова:* {profile['keywords'] or 'Не указано'}\n\n"
        f"⛔️ *Минус слова:* {profile['stop_words'] or 'Не указано'}\n\n"
        # f"🔔 *Подписка:* {profile['user_subscription'] or 'Отсутствует'}\n\n"
        f"*Выберите поле для редактирования:*"
    )
    return profile_text


@dp.callback_query(lambda call: call.data == "sources")
async def process_sources(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Profile.source)
    keyboard = await get_sources_keyboard(callback_query, state)

    await callback_query.message.edit_text(
        "🔔 Пожалуйста, отметьте источники, "
        "по которым хотите получать уведомления:\n\n",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: call.data == "categories")
async def process_categories(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Profile.category)
    keyboard = await get_categories_keyboard(callback_query, state)

    await callback_query.message.edit_text(
        "🔔 Пожалуйста, отметьте категории, "
        "по которым хотите получать уведомления:\n\n",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: call.data == "profile")
async def process_profile(callback_query: CallbackQuery, state: FSMContext) -> None:
    profile_text = await get_profile_data(callback_query, state)
    keyboard = await get_change_profile_keyboard()
    await callback_query.message.edit_text(profile_text, reply_markup=keyboard, parse_mode="Markdown")


@dp.message(Command("profile"))
async def process_profile(message: Message, state: FSMContext) -> None:
    profile_text = await get_profile_data(message, state)
    keyboard = await get_change_profile_keyboard()
    await message.answer(profile_text, reply_markup=keyboard, parse_mode="Markdown")


@dp.callback_query(lambda call: call.data == "change_name")
async def process_change_name(callback_query: CallbackQuery, state: FSMContext) -> None:
    buttons = [
        [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="back_profile")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(Profile.name)
    await callback_query.message.edit_text(
        "✍️ *Введите ваше имя:*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.message(Profile.name)
async def process_change_name(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "name", message.text)

    if status == 400:
        buttons = [
            [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="back_profile")],
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            (
                "⚠️ Что-то пошло не так. Обратите внимание, что имя не может превышать 255 символов.\n\n"
                "✍️ *Введите ваше имя:*"
            ),
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
        await state.set_state(Profile.name)
        return

    keyboard = await get_change_profile_keyboard()
    profile_text = await get_profile_data(message, state)

    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: call.data == "change_skills")
async def process_change_skills(callback_query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    skills = data["skills"]

    buttons = [
        [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="back_profile")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(Profile.skills)
    await callback_query.message.edit_text(
        f"*Текущее значение (нажмите, чтобы скопировать):* `{skills}`\n\n"
        "✍️ *Введите ваши навыки через запятую:*\n\n",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.message(Profile.skills)
async def process_change_skills(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "skills", message.text)

    if status == 400:
        buttons = [
            [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="back_profile")],
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            (
                "⚠️ Что-то пошло не так. Убедитесь, что строка не превышает 512 символов.\n\n"
                "✍️ *Введите ваши навыки через запятую:*"
            ),
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
        await state.set_state(Profile.skills)
        return

    keyboard = await get_change_profile_keyboard()
    profile_text = await get_profile_data(message, state)

    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: call.data == "change_summary")
async def process_change_summary(callback_query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    summary = data["summary"]

    buttons = [
        [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="back_profile")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(Profile.summary)
    await callback_query.message.edit_text(
        f"*Текущее значение (нажмите, чтобы скопировать):* `{summary}`\n\n"
        "✍️ *Расскажите немного о себе и вашей профессиональной деятельности:*\n\n",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.message(Profile.summary)
async def process_change_summary(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "summary", message.text)

    if status == 400:
        buttons = [
            [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="back_profile")],
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            (
                "⚠️ Что-то пошло не так. Убедитесь, что строка не превышает 1024 символа.\n\n"
                "✍️ *Расскажите немного о себе и вашей профессиональной деятельности:*"
            ),
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
        await state.set_state(Profile.summary)
        return

    keyboard = await get_change_profile_keyboard()
    profile_text = await get_profile_data(message, state)

    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: call.data == "change_experience")
async def process_change_experience(callback_query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    experience = data["experience"]

    buttons = [
        [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="back_profile")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(Profile.experience)
    await callback_query.message.edit_text(
        f"*Текущее значение (нажмите, чтобы скопировать):* `{experience}`\n\n"
        "✍️ *Поделитесь своим профессиональным опытом:*\n\n",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.message(Profile.experience)
async def process_change_experience(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "experience", message.text)

    if status == 400:
        buttons = [
            [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="back_profile")],
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            (
                "⚠️ Что-то пошло не так. Убедитесь, что строка не превышает 1024 символа.\n\n"
                "✍️ *Поделитесь своим профессиональным опытом:*"
            ),
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
        await state.set_state(Profile.experience)
        return

    keyboard = await get_change_profile_keyboard()
    profile_text = await get_profile_data(message, state)

    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: call.data == "change_hourly_rate")
async def process_change_hourly_rate(callback_query: CallbackQuery, state: FSMContext) -> None:
    buttons = [
        [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="back_profile")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(Profile.hourly_rate)
    await callback_query.message.edit_text(
        "✍️ *Введите вашу почасовую ставку:*",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@dp.message(Profile.hourly_rate)
async def process_change_hourly_rate(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "hourly_rate", message.text)

    if status == 400:
        buttons = [
            [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="back_profile")],
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            (
                "⚠️ Что-то пошло не так. Пожалуйста, введите корректное число.\n\n"
                "✍️ *Введите вашу почасовую ставку:*"
            ),
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
        await state.set_state(Profile.hourly_rate)
        return

    keyboard = await get_change_profile_keyboard()
    profile_text = await get_profile_data(message, state)

    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: call.data == "change_keywords")
async def process_change_keywords(callback_query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    keywords = data["keywords"]
    buttons = [
        [types.InlineKeyboardButton(text="🗑️️ Удалить ключевые слова", callback_data="delete_keywords")],
        [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="back_profile")],
    ]
    await state.set_state(Profile.keywords)
    await callback_query.message.edit_text(
        f"*Текущее значение (нажмите, чтобы скопировать):* `{keywords}`\n\n"
        "✍️ *Введите ключевые-слова:*",
        parse_mode="Markdown",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@dp.message(Profile.keywords)
async def process_change_keywords(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "keywords", message.text)

    if status == 400:
        buttons = [
            [types.InlineKeyboardButton(text="🗑️️ Удалить ключевые слова", callback_data="delete_keywords")],
            [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="back_profile")],
        ]
        await message.answer(
            (
                "⚠️ Что-то пошло не так. Убедитесь, что строка не превышает 2048 символов.\n\n"
                "✍️ *Введите ключевые-слова:*"
            ),
            parse_mode="Markdown",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        await state.set_state(Profile.keywords)
        return

    keyboard = await get_change_profile_keyboard()
    profile_text = await get_profile_data(message, state)

    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: call.data == "change_stop_words")
async def process_change_stop_words(callback_query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    stop_words = data["stop_words"]
    buttons = [
        [types.InlineKeyboardButton(text="🗑️️ Удалить минус слова", callback_data="delete_stop_words")],
        [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="back_profile")],
    ]
    await state.set_state(Profile.stop_words)
    await callback_query.message.edit_text(
        f"*Текущее значение (нажмите, чтобы скопировать):* `{stop_words}`\n\n"
        "✍️ *Введите минус-слова:*",
        parse_mode="Markdown",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@dp.callback_query(lambda call: call.data == "delete_stop_words")
async def process_delete_stop_words(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(callback_query, "stop_words", None)
    keyboard = await get_change_profile_keyboard()
    profile_text = await get_profile_data(callback_query, state)

    await callback_query.message.edit_text(
        profile_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: call.data == "delete_keywords")
async def process_delete_keywords(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(callback_query, "keywords", None)
    keyboard = await get_change_profile_keyboard()
    profile_text = await get_profile_data(callback_query, state)

    await callback_query.message.edit_text(
        profile_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: call.data == "back_profile")
async def process_back_profile(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    keyboard = await get_change_profile_keyboard()
    profile_text = await get_profile_data(callback_query, state)

    await callback_query.message.edit_text(
        profile_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.message(Profile.stop_words)
async def process_change_stop_words(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "stop_words", message.text)

    if status == 400:
        buttons = [
            [types.InlineKeyboardButton(text="🗑️️ Удалить минус-слова", callback_data="delete_stop_words")],
            [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="back_profile")],
        ]
        await message.answer(
            (
                "⚠️ Что-то пошло не так. Убедитесь, что строка не превышает 2048 символов.\n\n"
                "✍️ *Введите минус-слова:*"
            ),
            parse_mode="Markdown",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        await state.set_state(Profile.stop_words)
        return

    keyboard = await get_change_profile_keyboard()
    profile_text = await get_profile_data(message, state)

    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: re.match(r'analyze_order_pro_ai:\d+', call.data))
async def analyze_order_pro_ai(callback_query: CallbackQuery):
    project_id = int(callback_query.data.split(':')[1])
    message = await callback_query.message.reply(f'Выполняется анализ AI...')
    data, status = await api.projects_analyze(
        project_id,
        callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        delete_message_id=message.message_id,
    )


@dp.callback_query(lambda call: re.match(r"buy_gpt_requests:\d+", call.data))
async def process_buy_gpt_requests(callback_query: CallbackQuery):
    message_id = int(callback_query.data.split(":")[-1])

    await callback_query.message.delete()
    keyboard = await get_buy_gpt_requests_keyboard()

    caption = (
        "*PRO-подписка на месяц в подарок!\n"
        "**PRO-подписка на три месяца в подарок!\n\n"
        "Выберите один из доступных пакетов запросов:"
    )

    image_path = './buy_ai.jpg'

    await bot.send_photo(
        chat_id=callback_query.message.chat.id,
        photo=FSInputFile(image_path),
        caption=caption,
        reply_markup=keyboard,
        # reply_to_message_id=message_id
    )

@dp.callback_query(lambda call: re.match(r"buy_subscription:\d+", call.data))
async def process_buy_subscription(callback_query: CallbackQuery):
    message_id = int(callback_query.data.split(":")[-1])
    await callback_query.message.delete()

    keyboard = await get_buy_subscription_keyboard()

    caption = (
        "*10 AI-запросов в подарок!\n"
        "**30 AI-запросов в подарок!\n\n"
        "Выберите один из доступных вариантов подписки:"
    )

    image_path = './buy_pro.jpg'

    await bot.send_photo(
        chat_id=callback_query.message.chat.id,
        photo=FSInputFile(image_path),
        caption=caption,
        reply_markup=keyboard,
        # reply_to_message_id=message_id
    )


# @dp.callback_query(lambda call: re.match(r"buy_gpt_requests:\d+", call.data))
# async def buy_gpt_requests(callback_query: CallbackQuery):
#     requests_count = int(callback_query.data)


# @dp.message(Command("projects"))
# async def send_projects(message: Message, state: FSMContext):
#     response, _ = await api.user_create(message)
#     if not response.get("username"):
#         ...


def main():
    dp.startup.register(on_startup)

    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    main()
