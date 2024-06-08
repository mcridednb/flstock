from aiogram import Router, F, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import api
import callbacks
import keyboards
from states import Registration, Notifications

router = Router()


async def get_notifications_data(chat_id, state):
    profile, _ = await api.user_detail(chat_id)
    await state.set_data(profile)
    profile_text = (
        f"🏷️ *Ключевые слова:* {profile['keywords'] or 'Не указано'}\n\n"
        f"⛔️ *Минус слова:* {profile['stop_words'] or 'Не указано'}\n\n"
        f"*Выберите поле для редактирования:*"
    )
    return profile_text


@router.message(Command("notifications"))
async def process_notifications(message: Message, state: FSMContext) -> None:
    await state.clear()
    text = await get_notifications_data(message.from_user.id, state)
    keyboard = await keyboards.get_notifications_keyboard()
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(F.data == "notifications")
async def process_notifications(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    keyboard = await keyboards.get_notifications_keyboard()
    await callback_query.message.edit_text(
        text=await get_notifications_data(callback_query.from_user.id, state),
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(lambda call: call.data == "sources")
async def process_sources(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Notifications.source)
    keyboard = await keyboards.get_sources_keyboard(callback_query, state)

    await callback_query.message.edit_text(
        "*🔔 Пожалуйста, отметьте источники, "
        "по которым хотите получать уведомления:*\n\n",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(lambda call: call.data == "categories")
async def process_categories(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Notifications.category)
    keyboard = await keyboards.get_categories_keyboard(callback_query, state)

    await callback_query.message.edit_text(
        "*🔔 Пожалуйста, отметьте категории, "
        "по которым хотите получать уведомления:*\n\n",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(Registration.category, callbacks.Category.filter(F.action == callbacks.Action.set))
@router.callback_query(Notifications.category, callbacks.Category.filter(F.action == callbacks.Action.set))
async def process_category(
        callback_query: CallbackQuery,
        callback_data: callbacks.Category,
        state: FSMContext
) -> None:
    current_state = await state.get_state()
    states_map = {
        Registration.category: Registration.subcategory,
        Notifications.category: Notifications.subcategory,
    }
    await state.set_state(states_map[current_state])
    await state.set_data({
        "category": callback_data.code,
    })
    keyboard = await keyboards.get_subscriptions_keyboard(callback_query.from_user.id, callback_data.code)
    if len(keyboard.inline_keyboard) == 1:
        await callback_query.message.edit_text(
            "*😔 К сожалению, выбранная категория сейчас недоступна.\n"
            "Пожалуйста, выберите другую категорию.*",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await callback_query.message.edit_text(
            "*🔔 Пожалуйста, отметьте категории, "
            "по которым хотите получать уведомления:*\n\n",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )


@router.callback_query(Registration.subcategory, callbacks.Subcategory.filter(F.action == callbacks.Action.set))
@router.callback_query(Notifications.subcategory, callbacks.Subcategory.filter(F.action == callbacks.Action.set))
async def process_subcategory(
        callback_query: CallbackQuery,
        callback_data: callbacks.Subcategory,
        state: FSMContext
) -> None:
    response, status = await api.category_subscribe(callback_query.from_user.id, callback_data.code)
    if status == 400:
        await callback_query.answer(response[0])
        return

    data = await state.get_data()
    keyboard = await keyboards.get_subscriptions_keyboard(callback_query.from_user.id, data["category"])
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(Registration.source, callbacks.Source.filter(F.action == callbacks.Action.set))
@router.callback_query(Notifications.source, callbacks.Source.filter(F.action == callbacks.Action.set))
async def process_source(
        callback_query: CallbackQuery,
        callback_data: callbacks.Source,
        state: FSMContext
) -> None:
    response, status = await api.source_subscribe(callback_query.from_user.id, callback_data.code)
    if status == 400:
        await callback_query.answer(response[0])
        return

    keyboard = await keyboards.get_sources_keyboard(callback_query, state)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(lambda call: call.data == "change_keywords")
async def process_change_keywords(callback_query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    keywords = data["keywords"]
    buttons = [
        [types.InlineKeyboardButton(text="🗑️️ Удалить ключевые слова", callback_data="delete_keywords")],
        [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="notifications")],
    ]
    await state.set_state(Notifications.keywords)
    await callback_query.message.edit_text(
        f"*Текущее значение (нажмите, чтобы скопировать):* `{keywords}`\n\n"
        "✍️ *Введите ключевые-слова:*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.message(Notifications.keywords)
async def process_change_keywords(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "keywords", message.text)

    if status == 400:
        buttons = [
            [types.InlineKeyboardButton(text="🗑️️ Удалить ключевые слова", callback_data="delete_keywords")],
            [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="notifications")],
        ]
        await message.answer(
            "⚠️ Что-то пошло не так. Убедитесь, что строка не превышает 2048 символов.\n\n"
            "✍️ *Введите ключевые-слова:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        await state.set_state(Notifications.keywords)
        return

    keyboard = await keyboards.get_notifications_keyboard()
    text = await get_notifications_data(message.from_user.id, state)

    await message.answer(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(lambda call: call.data == "change_stop_words")
async def process_change_stop_words(callback_query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    stop_words = data["stop_words"]
    buttons = [
        [types.InlineKeyboardButton(text="🗑️️ Удалить минус слова", callback_data="delete_stop_words")],
        [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="notifications")],
    ]
    await state.set_state(Notifications.stop_words)
    await callback_query.message.edit_text(
        f"*Текущее значение (нажмите, чтобы скопировать):* `{stop_words}`\n\n"
        "✍️ *Введите минус-слова:*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.message(Notifications.stop_words)
async def process_change_stop_words(message: Message, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(message, "stop_words", message.text)

    if status == 400:
        buttons = [
            [types.InlineKeyboardButton(text="🗑️️ Удалить минус-слова", callback_data="delete_stop_words")],
            [types.InlineKeyboardButton(text="🚫 Отмена", callback_data="notifications")],
        ]
        await message.answer(
            "⚠️ Что-то пошло не так. Убедитесь, что строка не превышает 2048 символов.\n\n"
            "✍️ *Введите минус-слова:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        await state.set_state(Notifications.stop_words)
        return

    keyboard = await keyboards.get_notifications_keyboard()
    text = await get_notifications_data(message.from_user.id, state)

    await message.answer(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(lambda call: call.data == "delete_stop_words")
async def process_delete_stop_words(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(callback_query, "stop_words", None)
    await process_notifications(callback_query, state)


@router.callback_query(lambda call: call.data == "delete_keywords")
async def process_delete_keywords(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    _, status = await api.user_patch(callback_query, "keywords", None)
    await process_notifications(callback_query, state)
