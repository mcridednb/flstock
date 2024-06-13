from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import InlineKeyboardBuilder

import api
import callbacks
import keyboards

router = Router()


async def get_tasks_data(chat_id):
    tasks, _ = await api.tasks_list(chat_id)
    menu_text = (
        f"🪙 *Токены:* {profile['tokens']}\n\n"
        f"🔔 *Подписка:* {subscription or 'Отсутствует'}\n\n"
        f"📋 *Выберите действие, которое хотите выполнить:*"
    )
    return menu_text


@router.message(Command("tasks"))
async def process_tasks(message: Message, state: FSMContext) -> None:
    await state.clear()
    keyboard = await keyboards.get_menu_keyboard(message.message_id)
    await message.answer(
        text=await get_menu_data(message.from_user.id, state),
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(F.data == "tasks")
async def process_menu(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    keyboard = await keyboards.get_menu_keyboard(callback_query.message.message_id)
    await callback_query.message.edit_text(
        text=await get_menu_data(callback_query.from_user.id, state),
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )