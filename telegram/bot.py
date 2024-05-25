import os
import re
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from dotenv import load_dotenv
from loguru import logger

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

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


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


async def get_close_keyboard():
    buttons = [[types.InlineKeyboardButton(
        text="❌Закрыть",
        callback_data="close",
    )]]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_menu_keyboard():
    buttons = [[types.InlineKeyboardButton(
        text="👤 Редактировать профиль",
        callback_data="profile",
    )], [types.InlineKeyboardButton(
        text="📝 Редактировать категории",
        callback_data="categories",
    )], [types.InlineKeyboardButton(
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
        # [types.InlineKeyboardButton(text="💳 Купить подписку", callback_data="buy_subscription")],
        [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


async def on_startup(dispatcher: Dispatcher):
    pass


@dp.message(Command("start"))
async def send_welcome(message: Message, state: FSMContext):
    response, _ = await api.user_create(message)
    if not response.get("username"):
        await state.clear()
        keyboard = await get_menu_keyboard()
        await message.answer(
            text="📋 *Выберите нужное действие:*",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await state.set_state(Registration.category)
        keyboard = await get_categories_keyboard(message, state)
        await message.answer(
            "👋 *Добро пожаловать!*\n\n"
            "🔔 Пожалуйста, отметьте категории, "
            "по которым хотите получать уведомления:\n\n"
            "(Это можно будет изменить в настройках позднее)",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


@dp.callback_query(lambda call: call.data == "close")
async def process_close(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback_query.message.delete()


@dp.callback_query(lambda call: call.data == "back")
async def process_back(callback_query: CallbackQuery, state: FSMContext) -> None:
    keyboard = await get_categories_keyboard(callback_query, state)

    if await state.get_state() == Registration.subcategory:
        await state.set_state(Registration.category)
        await callback_query.message.edit_text(
            "👋 *Добро пожаловать!*\n\n"
            "🔔 Пожалуйста, отметьте категории, "
            "по которым хотите получать уведомления:\n\n"
            "(Это можно будет изменить в настройках позднее)",
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
        keyboard = await get_menu_keyboard()
        await callback_query.message.edit_text(
            text="📋 *Выберите действие, которое хотите выполнить:*",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


@dp.message(Command("menu"))
async def process_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    keyboard = await get_menu_keyboard()
    await message.answer(
        text="📋 *Выберите действие, которое хотите выполнить:*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: call.data == "next")
async def process_next(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback_query.message.edit_text(
        "🎉 Отлично! Теперь вы будете получать уведомления.\n\n"
        "🔔 Вы всегда можете изменить свои предпочтения в настройках.",
        reply_markup=await get_close_keyboard()
    )


@dp.callback_query(Registration.category)
async def process_category(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Registration.subcategory)
    await state.set_data({
        "category": callback_query.data
    })
    keyboard = await get_subscriptions_keyboard(callback_query.data, callback_query)
    await callback_query.message.edit_text(
        "👋 *Добро пожаловать!*\n\n"
        "🔔 Пожалуйста, отметьте категории, "
        "по которым хотите получать уведомления:\n\n"
        "(Это можно будет изменить в настройках позднее)",
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
    await api.category_subscribe(callback_query)
    data = await state.get_data()
    keyboard = await get_subscriptions_keyboard(data["category"], callback_query)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


@dp.callback_query(Profile.subcategory)
async def process_subcategory(callback_query: CallbackQuery, state: FSMContext) -> None:
    await api.category_subscribe(callback_query)
    data = await state.get_data()
    keyboard = await get_subscriptions_keyboard(data["category"], callback_query)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


async def get_profile_data(message):
    profile, _ = await api.user_detail(message)
    profile_text = (
        f"👤 *Имя:* {profile['name'] or 'Не указано'}\n\n"
        f"🛠️ *Навыки:* {profile['skills'] or 'Не указано'}\n\n"
        f"📝 *О себе:* {profile['summary'] or 'Не указано'}\n\n"
        f"💼 *Опыт:* {profile['experience'] or 'Не указано'}\n\n"
        f"⏰ *Ставка в час:* {profile['hourly_rate'] or 'Не указано'}\n\n"
        # f"🔔 *Подписка:* {profile['user_subscription'] or 'Отсутствует'}\n\n"
        f"*Выберите поле для редактирования:*"
    )
    return profile_text


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
    keyboard = await get_change_profile_keyboard()
    profile_text = await get_profile_data(callback_query)

    await callback_query.message.edit_text(
        profile_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: call.data == "change_name")
async def process_change_name(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Profile.name)
    await callback_query.message.edit_text(
        "✍️ *Введите ваше имя:*",
        reply_markup=None,
        parse_mode="Markdown"
    )


@dp.message(Profile.name)
async def process_change_name(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "name", message.text)

    if status == 400:
        await message.answer(
            (
                "⚠️ Что-то пошло не так. Обратите внимание, что имя не может превышать 255 символов.\n\n"
                "✍️ *Введите ваше имя:*"
            ),
            parse_mode="Markdown"
        )
        await state.set_state(Profile.name)
        return

    keyboard = await get_change_profile_keyboard()
    profile_text = await get_profile_data(message)

    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: call.data == "change_skills")
async def process_change_skills(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Profile.skills)
    await callback_query.message.edit_text(
        "✍️ *Введите ваши навыки через запятую:*\n\n"
        "⚠️ Пожалуйста, помните, что вся строка не должна превышать 512 символов.",
        reply_markup=None,
        parse_mode="Markdown"
    )


@dp.message(Profile.skills)
async def process_change_skills(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "skills", message.text)

    if status == 400:
        await message.answer(
            (
                "⚠️ Что-то пошло не так. Убедитесь, что строка не превышает 512 символов.\n\n"
                "✍️ *Введите ваши навыки через запятую:*"
            ),
            parse_mode="Markdown"
        )
        await state.set_state(Profile.skills)
        return

    keyboard = await get_change_profile_keyboard()
    profile_text = await get_profile_data(message)

    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: call.data == "change_summary")
async def process_change_summary(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Profile.summary)
    await callback_query.message.edit_text(
        "✍️ *Расскажите немного о себе и вашей профессиональной деятельности:*\n\n"
        "⚠️ Пожалуйста, помните, что текст не должен превышать 1024 символа.",
        reply_markup=None,
        parse_mode="Markdown"
    )


@dp.message(Profile.summary)
async def process_change_summary(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "summary", message.text)

    if status == 400:
        await message.answer(
            (
                "⚠️ Что-то пошло не так. Убедитесь, что строка не превышает 1024 символа.\n\n"
                "✍️ *Расскажите немного о себе и вашей профессиональной деятельности:*"
            ),
            parse_mode="Markdown"
        )
        await state.set_state(Profile.summary)
        return

    keyboard = await get_change_profile_keyboard()
    profile_text = await get_profile_data(message)

    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: call.data == "change_experience")
async def process_change_experience(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Profile.experience)
    await callback_query.message.edit_text(
        "✍️ *Поделитесь своим профессиональным опытом:*\n\n"
        "⚠️ Пожалуйста, помните, что текст не должен превышать 1024 символа.",
        reply_markup=None,
        parse_mode="Markdown"
    )


@dp.message(Profile.experience)
async def process_change_experience(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "experience", message.text)

    if status == 400:
        await message.answer(
            (
                "⚠️ Что-то пошло не так. Убедитесь, что строка не превышает 1024 символа.\n\n"
                "✍️ *Поделитесь своим профессиональным опытом:*"
            ),
            parse_mode="Markdown"
        )
        await state.set_state(Profile.experience)
        return

    keyboard = await get_change_profile_keyboard()
    profile_text = await get_profile_data(message)

    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: call.data == "change_hourly_rate")
async def process_change_hourly_rate(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Profile.hourly_rate)
    await callback_query.message.edit_text(
        "💰 *Введите вашу почасовую ставку:*",
        reply_markup=None,
        parse_mode="Markdown"
    )


@dp.message(Profile.hourly_rate)
async def process_change_hourly_rate(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "hourly_rate", message.text)

    if status == 400:
        await message.answer(
            (
                "❗ Что-то пошло не так. Пожалуйста, введите корректное число.\n\n"
                "💰 *Введите вашу почасовую ставку:*"
            ),
            parse_mode="Markdown"
        )
        await state.set_state(Profile.hourly_rate)
        return

    keyboard = await get_change_profile_keyboard()
    profile_text = await get_profile_data(message)

    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda call: re.match(r'analyze_order_ai:\d+', call.data))
async def analyze_order_ai(callback_query: CallbackQuery):
    project_id = int(callback_query.data.split(':')[1])
    data, status = await api.projects_analyze(
        project_id,
        callback_query.from_user.id,
        callback_query.message.message_id,
        "base"
    )
    await callback_query.answer(f'Проект отправлен на анализ AI')


@dp.callback_query(lambda call: re.match(r'analyze_order_pro_ai:\d+', call.data))
async def analyze_order_pro_ai(callback_query: CallbackQuery):
    project_id = int(callback_query.data.split(':')[1])
    data, status = await api.projects_analyze(
        project_id,
        callback_query.from_user.id,
        callback_query.message.message_id,
        "pro"
    )
    await callback_query.answer(f'Проект отправлен на анализ PRO AI')


async def main():
    await dp.start_polling(bot, on_startup=on_startup)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
