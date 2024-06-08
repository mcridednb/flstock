from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.deep_linking import create_start_link

import api
import keyboards
from handlers.menu import get_menu_data
from states import Registration

router = Router()


def check(member):
    return member.status != "left"


# async def check_channels(message: Message):
#     builder = InlineKeyboardBuilder()
#     if not check(await message.bot.get_chat_member("-1002216378515", message.from_user.id)):
#         builder.button(
#             text="Новости нашего проекта", url="https://t.me/freelancerai_info"
#         )
#         me = await message.bot.get_me()
#         builder.button(
#             text="✅ Проверить", url=f"https://t.me/{me.username}?start="
#         )
#         builder.adjust(1)
#         await message.bot.send_message(
#             message.from_user.id,
#             "Для работы с ботом нужно подписаться на:",
#             reply_markup=builder.as_markup()
#         )
#         return False
#
#     return True


@router.message(CommandStart(deep_link=True, deep_link_encoded=True))
async def send_welcome_deep(message: Message, state: FSMContext, command: CommandObject):
    referrer = command.args
    await send_welcome(message, state, referrer)


@router.message(CommandStart())
async def send_welcome(message: Message, state: FSMContext, referrer=None):
    response, status = await api.user_detail(message.from_user.id)
    if status == 404 or not response["registration_completed"]:
        response, status = await api.user_create(message, referrer)
        await state.set_state(Registration.source)
        keyboard = await keyboards.get_sources_keyboard(message, state)
        await message.answer(
            "👋 *Добро пожаловать!*\n\n"
            "🔔 Пожалуйста, отметьте источники, "
            "по которым хотите получать уведомления:\n\n"
            "(Это можно будет изменить в настройках позднее)",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await state.clear()
        keyboard = await keyboards.get_menu_keyboard(message.message_id)
        await message.answer(
            text=await get_menu_data(message.from_user.id, state),
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


@router.message(Command("link"))
async def process_link(message: Message, state: FSMContext) -> None:
    link = await create_start_link(message.bot, str(message.from_user.id), encode=True)
    await state.clear()
    await message.answer(
        text=f"📋 Ваша реферальная ссылка: \n{link}",
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("balance"))
async def process_balance(message: Message, state: FSMContext) -> None:
    await state.clear()
    keyboard = await keyboards.get_balance_keyboard(message.message_id)
    await message.answer(
        text=await get_menu_data(message.from_user.id, state),
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )

# @dp.message(Command("projects"))
# async def send_projects(message: Message, state: FSMContext):
#     response, _ = await api.user_create(message)
#     if not response.get("username"):
#         ...

