from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import api
import callbacks
import states

router = Router()

#         f"👤 *Имя:* {profile['name'] or 'Не указано'}\n\n"
#         f"🛠️ *Навыки:* {profile['skills'] or 'Не указано'}\n\n"
#         f"📝 *О себе:* {profile['summary'] or 'Не указано'}\n\n"
#         f"💼 *Опыт:* {profile['experience'] or 'Не указано'}\n\n"
#         f"⏰ *Ставка в час:* {profile['hourly_rate'] or 'Не указано'}\n\n"


async def check_user_data(chat_id):
    user_data, _ = await api.user_detail(chat_id)
    text = []
    if not user_data["name"]:
        text.append(">\n> — Не указано имя")
    if not user_data["skills"]:
        text.append(">\n> — Не указаны навыки")
    if not user_data["summary"]:
        text.append(">\n> — Не заполнена основная информация")
    if not user_data["experience"]:
        text.append(">\n> — Не указан опыт")
    if not user_data["hourly_rate"]:
        text.append(">\n> — Не указана ставка в час")
    if text:
        text.insert(0, ">⚠️ Не заполнена информация в профиле:")
        text.append(
            ">\n>💡 Для получения более качественного отклика, рекомендуем заполнить поля в профиле "
            "или предоставить эту информацию в качестве примечания\."
        )
    return "\n".join(text)


@router.callback_query(callbacks.Project.filter(F.action == callbacks.Action.response))
async def process_gpt_response(
    callback_query: CallbackQuery,
    callback_data: callbacks.Project,
    state: FSMContext
):
    await state.set_state(states.GPT.start_response)

    warning_text = await check_user_data(callback_query.from_user.id)

    builder = InlineKeyboardBuilder()
    builder.button(
        text="Пропустить ➡️",
        callback_data=callbacks.GPTRequest(
            action=callbacks.Action.start,
            project_id=callback_data.id,
        )
    )
    builder.button(text="🚫 Отмена", callback_data="close")
    builder.adjust(1)
    message = await callback_query.message.reply(
        text=warning_text + "✏️ *Напишите своё примечание для ИИ:*\n\n"
             "💡 Расскажите про релевантный опыт, или предоставьте любую другую информацию, "
             "которую нужно учесть при генерации отклика\.\n\n"
             "↘️ *Можно пропустить*",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    await state.set_data({
        "project_id": callback_data.id,
        "message_id": callback_query.message.message_id,
        "request_type": callback_data.action,
        "delete_message_id": message.message_id,
    })


@router.callback_query(states.GPT.start_response, callbacks.GPTRequest.filter(F.action == callbacks.Action.start))
async def process_gpt_response(
    callback_query: CallbackQuery,
    callback_data: callbacks.Project,
    state: FSMContext
):
    data = await state.get_data()

    builder = InlineKeyboardBuilder()
    builder.button(
        text="⚠️ Сообщить об ошибке",
        callback_data=callbacks.GPTRequest(
            action=callbacks.Action.complain,
            project_id=data["project_id"],
        )
    )
    message = await callback_query.message.edit_text(
        text="🔄 *Формируем отклик...*\n\n"
             "⏳ *Пожалуйста, подождите, это может занять несколько секунд.*",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN,
    )
    await api.gpt_request_create(
        data["project_id"],
        callback_query.from_user.id,
        message_id=data["message_id"],
        delete_message_id=message.message_id,
        request_type=data["request_type"],
    )

    await state.clear()


@router.message(states.GPT.start_response)
async def process_gpt_response(message: Message, state: FSMContext) -> None:
    data = await state.get_data()

    additional_info = message.text

    await message.bot.delete_message(message.from_user.id, data["delete_message_id"])
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⚠️ Сообщить об ошибке",
        callback_data=callbacks.GPTRequest(
            action=callbacks.Action.complain,
            project_id=data["project_id"],
        )
    )
    message = await message.answer(
        text="🔄 *Формируем отклик...*\n\n"
             "⏳ *Пожалуйста, подождите, это может занять несколько секунд.*",
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


@router.callback_query(callbacks.Project.filter(F.action == callbacks.Action.analyze))
async def process_gpt_analyze(
    callback_query: CallbackQuery,
    callback_data: callbacks.Project,
    state: FSMContext
):
    await state.set_state(states.GPT.start_analyze)

    warning_text = await check_user_data(callback_query.from_user.id)

    builder = InlineKeyboardBuilder()
    builder.button(
        text="Пропустить ➡️",
        callback_data=callbacks.GPTRequest(
            action=callbacks.Action.start,
            project_id=callback_data.id,
        )
    )
    builder.button(text="🚫 Отмена", callback_data="close")
    builder.adjust(1)
    message = await callback_query.message.reply(
        text=warning_text + "✏️ *Напишите своё примечание для ИИ:*\n\n"
             "💡 Расскажите про релевантный опыт, или про желаемые инструменты, для решения задачи, "
             "или предоставьте любую другую информацию, "
             "которую необходимо учесть при генерации решения задачи\.\n\n"
             "↘️ *Можно пропустить*",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    await state.set_data({
        "project_id": callback_data.id,
        "message_id": callback_query.message.message_id,
        "request_type": callback_data.action,
        "delete_message_id": message.message_id,
    })


@router.callback_query(states.GPT.start_analyze, callbacks.GPTRequest.filter(F.action == callbacks.Action.start))
async def process_gpt_analyze(
    callback_query: CallbackQuery,
    callback_data: callbacks.Project,
    state: FSMContext
):
    data = await state.get_data()

    builder = InlineKeyboardBuilder()
    builder.button(
        text="⚠️ Сообщить об ошибке",
        callback_data=callbacks.GPTRequest(
            action=callbacks.Action.complain,
            project_id=data["project_id"],
        )
    )
    message = await callback_query.message.edit_text(
        text="⚙️ *Анализируем задачу...*\n\n"
             "⏳ *Пожалуйста, подождите, это может занять несколько секунд.*",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN,
    )
    await api.gpt_request_create(
        data["project_id"],
        callback_query.from_user.id,
        message_id=data["message_id"],
        delete_message_id=message.message_id,
        request_type=data["request_type"],
    )

    await state.clear()


@router.message(states.GPT.start_analyze)
async def process_gpt_response(message: Message, state: FSMContext) -> None:
    data = await state.get_data()

    additional_info = message.text

    await message.bot.delete_message(message.from_user.id, data["delete_message_id"])
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⚠️ Сообщить об ошибке",
        callback_data=callbacks.GPTRequest(
            action=callbacks.Action.complain,
            project_id=data["project_id"],
        )
    )
    message = await message.answer(
        text="⚙️ *Анализируем задачу...*\n\n"
             "⏳ *Пожалуйста, подождите, это может занять несколько секунд.*",
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
