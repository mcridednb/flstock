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


@router.message(Command("link"))
async def process_link(message: Message, state: FSMContext) -> None:
    await state.clear()
    link = await create_start_link(message.bot, str(message.from_user.id), encode=True)
    link = link.replace('.', '\.').replace("=", "\=").replace("_", "\_")
    await message.answer(
        text=(
            "🎁 *Приглашай друзей и получай бонусы\!*\n\n"
            "Поделись этой ссылкой с друзьями, и вы оба получите бонусные токены\!\n\n"
            "👥 *За каждого друга, который зарегистрируется по твоей ссылке, ты получишь 10 токенов\.*\n\n"
            "🎁 *Твой друг также получит 10 токенов\.*\n\n"
            "🔗 *Твоя реферальная ссылка:* \n\n"
            f"{link}"
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=await keyboards.get_close_keyboard()
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

