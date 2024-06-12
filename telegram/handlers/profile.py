from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import api
import keyboards
from states import Profile

router = Router()


async def get_profile_data(chat_id, state):
    profile, _ = await api.user_detail(chat_id)
    await state.set_data(profile)
    profile_text = (
        f"👤 *Имя:* {profile['name'] or 'Не указано'}\n\n"
        f"🛠️ *Навыки:* {profile['skills'] or 'Не указано'}\n\n"
        f"📝 *О себе:* {profile['summary'] or 'Не указано'}\n\n"
        f"💼 *Опыт:* {profile['experience'] or 'Не указано'}\n\n"
        f"⏰ *Ставка в час:* {profile['hourly_rate'] or 'Не указано'}\n\n"
        f"*Выберите поле для редактирования:*"
    )
    return profile_text


@router.message(Command("profile"))
async def process_profile(message: Message, state: FSMContext) -> None:
    await state.clear()
    profile_text = await get_profile_data(message.from_user.id, state)
    keyboard = await keyboards.get_change_profile_keyboard()
    await message.answer(profile_text, reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(lambda call: call.data == "profile")
async def process_profile(callback_query: CallbackQuery, state: FSMContext) -> None:
    profile_text = await get_profile_data(callback_query.from_user.id, state)
    keyboard = await keyboards.get_change_profile_keyboard()
    await callback_query.message.edit_text(profile_text, reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(lambda call: call.data == "change_name")
async def process_change_name(callback_query: CallbackQuery, state: FSMContext) -> None:
    buttons = [
        [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="profile")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(Profile.name)
    await callback_query.message.edit_text(
        "✍️ *Введите ваше имя:*",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.message(Profile.name)
async def process_change_name(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "name", message.text)

    if status == 400:
        buttons = [
            [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="profile")],
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            "⚠️ Что-то пошло не так. Обратите внимание, что имя не может превышать 255 символов.\n\n"
            "✍️ *Введите ваше имя:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
        )
        await state.set_state(Profile.name)
        return

    keyboard = await keyboards.get_change_profile_keyboard()
    profile_text = await get_profile_data(message.from_user.id, state)

    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(lambda call: call.data == "change_skills")
async def process_change_skills(callback_query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    skills = data["skills"]

    buttons = [
        [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="profile")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(Profile.skills)
    await callback_query.message.edit_text(
        f"*Текущее значение (нажмите, чтобы скопировать):* `{skills}`\n\n"
        "✍️ *Введите ваши навыки через запятую:*\n\n",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.message(Profile.skills)
async def process_change_skills(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "skills", message.text)

    if status == 400:
        buttons = [
            [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="profile")],
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            "⚠️ Что-то пошло не так. Убедитесь, что строка не превышает 512 символов.\n\n"
            "✍️ *Введите ваши навыки через запятую:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
        )
        await state.set_state(Profile.skills)
        return

    keyboard = await keyboards.get_change_profile_keyboard()
    profile_text = await get_profile_data(message.from_user.id, state)

    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(lambda call: call.data == "change_summary")
async def process_change_summary(callback_query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    summary = data["summary"]

    buttons = [
        [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="profile")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(Profile.summary)
    await callback_query.message.edit_text(
        f"*Текущее значение (нажмите, чтобы скопировать):* `{summary}`\n\n"
        "✍️ *Расскажите немного о себе и вашей профессиональной деятельности:*\n\n",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.message(Profile.summary)
async def process_change_summary(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "summary", message.text)

    if status == 400:
        buttons = [
            [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="profile")],
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            "⚠️ Что-то пошло не так. Убедитесь, что строка не превышает 1024 символа.\n\n"
            "✍️ *Расскажите немного о себе и вашей профессиональной деятельности:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
        )
        await state.set_state(Profile.summary)
        return

    keyboard = await keyboards.get_change_profile_keyboard()
    profile_text = await get_profile_data(message.from_user.id, state)

    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(lambda call: call.data == "change_experience")
async def process_change_experience(callback_query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    experience = data["experience"]

    buttons = [
        [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="profile")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(Profile.experience)
    await callback_query.message.edit_text(
        f"*Текущее значение (нажмите, чтобы скопировать):* `{experience}`\n\n"
        "✍️ *Поделитесь своим профессиональным опытом:*\n\n",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.message(Profile.experience)
async def process_change_experience(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "experience", message.text)

    if status == 400:
        buttons = [
            [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="profile")],
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            "⚠️ Что-то пошло не так. Убедитесь, что строка не превышает 1024 символа.\n\n"
            "✍️ *Поделитесь своим профессиональным опытом:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
        )
        await state.set_state(Profile.experience)
        return

    keyboard = await keyboards.get_change_profile_keyboard()
    profile_text = await get_profile_data(message.from_user.id, state)

    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(lambda call: call.data == "change_hourly_rate")
async def process_change_hourly_rate(callback_query: CallbackQuery, state: FSMContext) -> None:
    buttons = [
        [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="profile")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(Profile.hourly_rate)
    await callback_query.message.edit_text(
        "✍️ *Введите вашу почасовую ставку:*",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.message(Profile.hourly_rate)
async def process_change_hourly_rate(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "hourly_rate", message.text)

    if status == 400:
        buttons = [
            [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="profile")],
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            "⚠️ Что-то пошло не так. Пожалуйста, введите корректное число.\n\n"
            "✍️ *Введите вашу почасовую ставку:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
        )
        await state.set_state(Profile.hourly_rate)
        return

    keyboard = await keyboards.get_change_profile_keyboard()
    profile_text = await get_profile_data(message.from_user.id, state)

    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )
