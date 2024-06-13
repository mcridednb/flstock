from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import keyboards
import states

router = Router()


@router.message(Command("support"))
async def process_support(message: Message, state: FSMContext) -> None:
    await state.clear()
    keyboard = await keyboards.get_close_keyboard()
    await message.answer(
        text="Напишите замечания / пожелания в сообщении ниже:",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )
    await state.set_state(states.Menu.support)


@router.callback_query(F.data == "support")
async def process_support(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    keyboard = await keyboards.get_close_keyboard()
    await callback_query.message.answer(
        text="Напишите замечания / пожелания в сообщении ниже:",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )
    await state.set_state(states.Menu.support)


@router.message(states.Menu.support)
async def send_support_message(message: Message, state: FSMContext):
    text = (
        f"📩 Сообщение в поддержку:\n"
        f"🧓 Пользователь: {message.from_user.id}\n\n"
        f"{message.text}"
    )
    await message.bot.send_message(
        chat_id=-1002238232891,
        text=text,
        message_thread_id=24,
    )
    keyboard = await keyboards.get_close_keyboard()
    await state.clear()
    await message.answer(
        "*Спасибо за ваше обращение!*",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )
