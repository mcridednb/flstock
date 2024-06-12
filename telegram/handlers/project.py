from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder

import api
import callbacks
import states

router = Router()


async def check_user_data(user_data):
    text = []
    if not user_data["name"]:
        text.append(">\n> — Не указано имя")
    if not user_data["skills"]:
        text.append("> — Не указаны навыки")
    if not user_data["summary"]:
        text.append("> — Не заполнена основная информация")
    if not user_data["experience"]:
        text.append("> — Не указан опыт")
    if not user_data["hourly_rate"]:
        text.append("> — Не указана ставка в час")
    if text:
        text.insert(0, ">⚠️ Не заполнена информация в профиле:")
        text.append(
            ">\n>💡 Для получения более качественного отклика, рекомендуем заполнить поля в профиле "
            "или предоставить эту информацию в качестве примечания\.\n"
            ">\n>Редактировать профиль: /profile\n\n\n"
        )
    return "\n".join(text)


async def process_phone(message, state, add_text=""):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="☎️ Отправить номер телефона", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.reply(
        "ℹ️ *Для использования функционала AI — необходимо подтвердить номер телефона.*" + add_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )
    await state.set_state(states.GPT.phone)


@router.message(states.GPT.phone)
async def send_phone(message: Message, state: FSMContext):
    if not message.contact:
        await process_phone(
            message, state, "\n\n*Убедитесь, что вы отправили номер телефона нажав на кнопку ниже ⬇️️*"
        )
        return

    await api.user_patch(message, "phone", message.contact.phone_number)

    data = await state.get_data()
    user_data = data["user_data"]

    warning_text = await check_user_data(user_data)

    builder = InlineKeyboardBuilder()
    builder.button(
        text="Пропустить ➡️",
        callback_data=callbacks.GPTRequest(
            type=data["request_type"],
            action=callbacks.Action.start,
            project_id=data["project_id"],
            message_id=data["message_id"],
        )
    )
    builder.button(text="🚫 Отмена", callback_data="close")
    builder.adjust(1)

    if data["request_type"] == "response":
        text = (
                "⚙️ *Генерация отклика\.\.\.*\n\n"
                + warning_text +
                "📝 Шаг 1 из 2: Примечание к отклику\n\n"
                "\n✏️ *Напишите своё примечание для ИИ:*\n\n"
                "💡 Расскажите про релевантный опыт, или предоставьте любую другую информацию, "
                "которую нужно учесть при генерации отклика\.\n\n"
                "↘️ *Можно пропустить*"
        )
        await state.set_state(states.GPT.start_response)
        message_to_delete = await message.answer(
            "👍 *Отлично.*\n"
            "Продолжаем генерацию отклика...",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.MARKDOWN,
        )
        await message_to_delete.delete()
    else:
        text = (
                "⚙️ *Генерация отчёта\.\.\.*\n\n"
                + warning_text +
                "📝 Шаг 1 из 2: Примечание к генерации отчёта\n\n"
                "💡 Расскажите про релевантный опыт, или про инструменты, "
                "которые планируете использовать при выполнении заказа, или предоставьте любую другую информацию, "
                "которую нужно учесть при генерации отчёта по заказу\.\n\n"
                "↘️ *Можно пропустить*"
        )
        await state.set_state(states.GPT.start_analyze)
        message_to_delete = await message.answer(
            "👍 *Отлично.* \n"
            "Продолжаем генерацию отчёта...",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.MARKDOWN,
        )
        await message_to_delete.delete()
    message = await message.bot.send_message(
        message.from_user.id,
        text,
        reply_to_message_id=data["message_id"],
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    await state.update_data({"delete_message_id": message.message_id})


@router.callback_query(callbacks.Project.filter(F.type == callbacks.Type.response))
async def process_gpt_response(
    callback_query: CallbackQuery,
    callback_data: callbacks.Project,
    state: FSMContext
):
    gpt_map = {
        callbacks.Type.response: states.GPT.start_response,
        callbacks.Type.analyze: states.GPT.start_analyze,
    }
    await state.set_state(gpt_map[callback_data.type])

    user_data, _ = await api.user_detail(callback_query.from_user.id)

    data = {
        "user_data": user_data,
        "project_id": callback_data.id,
        "message_id": callback_query.message.message_id,
        "request_type": callback_data.type,
    }
    await state.set_data(data)

    if not user_data.get("phone"):
        await process_phone(callback_query.message, state)
        return

    warning_text = await check_user_data(user_data)

    builder = InlineKeyboardBuilder()
    builder.button(
        text="Пропустить ➡️",
        callback_data=callbacks.GPTRequest(
            type=callback_data.type,
            action=callbacks.Action.start,
            project_id=callback_data.id,
            message_id=callback_query.message.message_id,
        )
    )
    builder.button(text="🚫 Отмена", callback_data="close")
    builder.adjust(1)
    message = await callback_query.message.reply(
        text=(
            "⚙️ *Генерация отклика\.\.\.*\n\n"
            + warning_text +
            "📝 Шаг 1 из 2: Примечание к отклику\n\n"
            "💡 Расскажите про релевантный опыт, или предоставьте любую другую информацию, "
            "которую нужно учесть при генерации отклика\.\n\n"
            "↘️ *Можно пропустить*"
        ),
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    await state.update_data({"delete_message_id": message.message_id})


@router.callback_query(
    callbacks.GPTRequest.filter((F.type == callbacks.Type.response) & (F.action == callbacks.Action.start))
)
async def process_gpt_response_start(
        callback_query: CallbackQuery,
        callback_data: callbacks.GPTRequest,
        state: FSMContext
):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⚠️ Сообщить об ошибке",
        callback_data=callbacks.GPTRequest(
            type=callbacks.Type.complain,
            project_id=callback_data.project_id,
        )
    )
    message = await callback_query.message.edit_text(
        text=(
            "⚙️ *Генерация отклика...*\n\n"
            "📝 Шаг 2 из 2: Анализ заказа\n\n"
            "⏳ *Анализируем данные, пожалуйста, подождите...*"
        ),
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN,
    )
    await api.gpt_request_create(
        callback_data.project_id,
        callback_query.from_user.id,
        message_id=callback_data.message_id,
        delete_message_id=message.message_id,
        request_type=callback_data.type,
    )

    await state.clear()


@router.message(states.GPT.start_response)
async def process_gpt_response_with_add_info(message: Message, state: FSMContext) -> None:
    data = await state.get_data()

    additional_info = message.text

    await message.bot.delete_message(message.from_user.id, data["delete_message_id"])
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⚠️ Сообщить об ошибке",
        callback_data=callbacks.GPTRequest(
            type=callbacks.Type.complain,
            project_id=data["project_id"],
        )
    )
    message = await message.answer(
        text=(
            "⚙️ *Генерация отклика...*\n\n"
            "📝 Шаг 2 из 2: Анализ заказа\n\n"
            "⏳ *Анализируем данные, пожалуйста, подождите...*"
        ),
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN,
    )
    await api.gpt_request_create(
        data["project_id"],
        message.chat.id,
        message_id=data["message_id"],
        delete_message_id=message.message_id,
        request_type=data["request_type"],
        additional_info=additional_info,
    )

    await state.clear()


@router.callback_query(callbacks.Project.filter(F.type == callbacks.Type.analyze))
async def process_gpt_analyze(
        callback_query: CallbackQuery,
        callback_data: callbacks.Project,
        state: FSMContext
):
    await state.set_state(states.GPT.start_analyze)

    user_data, _ = await api.user_detail(callback_query.from_user.id)

    data = {
        "user_data": user_data,
        "project_id": callback_data.id,
        "message_id": callback_query.message.message_id,
        "request_type": callback_data.type,
    }
    await state.set_data(data)

    if not user_data.get("phone"):
        await process_phone(callback_query.message, state)
        return

    warning_text = await check_user_data(user_data)

    builder = InlineKeyboardBuilder()
    builder.button(
        text="Пропустить ➡️",
        callback_data=callbacks.GPTRequest(
            type=callback_data.type,
            action=callbacks.Action.start,
            project_id=callback_data.id,
            message_id=callback_query.message.message_id,
        )
    )
    builder.button(text="🚫 Отмена", callback_data="close")
    builder.adjust(1)
    text = (
            "⚙️ *Генерация отчёта\.\.\.*\n\n"
            + warning_text +
            "📝 Шаг 1 из 2: Примечание к отчёту\n\n"
            "💡 Расскажите про релевантный опыт, или про инструменты, "
            "которые планируете использовать при выполнении заказа, или предоставьте любую другую информацию, "
            "которую нужно учесть при генерации отчёта по заказу\.\n\n"
            "↘️ *Можно пропустить*"
    )
    message = await callback_query.message.reply(
        text=text,
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    await state.update_data({"delete_message_id": message.message_id})


@router.callback_query(
    callbacks.GPTRequest.filter((F.type == callbacks.Type.analyze) & (F.action == callbacks.Action.start))
)
async def process_gpt_analyze_start(
        callback_query: CallbackQuery,
        callback_data: callbacks.GPTRequest,
        state: FSMContext
):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⚠️ Сообщить об ошибке",
        callback_data=callbacks.GPTRequest(
            type=callbacks.Type.complain,
            project_id=callback_data.project_id,
        )
    )
    message = await callback_query.message.edit_text(
        text=(
            "⚙️ *Генерация отчёта...*\n\n"
            "📝 Шаг 2 из 2: Анализ заказа\n\n"
            "⏳ *Анализируем данные, пожалуйста, подождите...*"
        ),
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN,
    )
    await api.gpt_request_create(
        callback_data.project_id,
        callback_query.from_user.id,
        message_id=callback_data.message_id,
        delete_message_id=message.message_id,
        request_type=callback_data.type,
    )

    await state.clear()


@router.message(states.GPT.start_analyze)
async def process_gpt_response_with_add_info(message: Message, state: FSMContext) -> None:
    data = await state.get_data()

    additional_info = message.text

    await message.bot.delete_message(message.from_user.id, data["delete_message_id"])
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⚠️ Сообщить об ошибке",
        callback_data=callbacks.GPTRequest(
            type=callbacks.Type.complain,
            project_id=data["project_id"],
        )
    )
    message = await message.answer(
        text=(
            "⚙️ *Генерация отчёта...*\n\n"
            "📝 Шаг 2 из 2: Анализ заказа\n\n"
            "⏳ *Анализируем данные, пожалуйста, подождите...*"
        ),
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN,
        reply_to_message_id=data["message_id"],
    )
    await api.gpt_request_create(
        data["project_id"],
        message.chat.id,
        message_id=data["message_id"],
        delete_message_id=message.message_id,
        request_type=data["request_type"],
        additional_info=additional_info,
    )

    await state.clear()
