from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import api
import keyboards
from states import Registration, Profile, Notifications

router = Router()


@router.callback_query(lambda call: call.data == "back")
async def process_back(callback_query: CallbackQuery, state: FSMContext) -> None:
    keyboard = await keyboards.get_categories_keyboard(callback_query, state)

    if await state.get_state() == Notifications.subcategory:
        await state.set_state(Notifications.category)
        await callback_query.message.edit_text(
            "🔔 Пожалуйста, отметьте категории, "
            "по которым хотите получать уведомления:\n\n",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await state.clear()
        keyboard = await keyboards.get_menu_keyboard(callback_query.message.message_id)
        await callback_query.message.edit_text(
            text="📋 *Выберите действие, которое хотите выполнить:*",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )


@router.callback_query(lambda call: call.data == "close")
async def process_close(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback_query.message.delete()
