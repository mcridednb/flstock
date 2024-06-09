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


async def get_menu_data(chat_id, state):
    profile, _ = await api.user_detail(chat_id)
    await state.set_data(profile)
    subscription = profile.get("subscription")
    if subscription:
        subscription = f"до {subscription}"
    menu_text = (
        f"🪙 *Токены:* {profile['tokens']}\n\n"
        f"🔔 *Подписка:* {subscription or 'Отсутствует'}\n\n"
        f"📋 *Выберите действие, которое хотите выполнить:*"
    )
    return menu_text


@router.message(Command("menu"))
async def process_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    keyboard = await keyboards.get_menu_keyboard(message.message_id)
    await message.answer(
        text=await get_menu_data(message.from_user.id, state),
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(F.data == "menu")
async def process_menu(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    keyboard = await keyboards.get_menu_keyboard(callback_query.message.message_id)
    await callback_query.message.edit_text(
        text=await get_menu_data(callback_query.from_user.id, state),
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(F.data == "referral")
async def process_referral(callback_query: CallbackQuery, state: FSMContext) -> None:
    link = await create_start_link(callback_query.bot, str(callback_query.from_user.id), encode=True)
    await state.clear()
    link = link.replace('.', '\.').replace("=", "\=").replace("_", "\_")
    await callback_query.message.answer(
        text=(
            "🎁 *Получай бонусы за друзей\!*\n\n"
            "Поделитесь этой ссылкой с друзьями, и вы оба получите бонусные токены\!\n\n"
            "👥 *За каждого друга, который зарегистрируется по вашей ссылке, вы получите 10 токенов\.*\n\n"
            "🎁 *Ваш друг также получит 10 токенов\.*\n\n"
            "🔗 *Ваша реферальная ссылка:* \n\n"
            f"{link}"
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=await keyboards.get_close_keyboard()
    )


@router.callback_query(callbacks.Token.filter(F.action == callbacks.Action.get))
async def process_buy_tokens(callback_query: CallbackQuery):
    keyboard = await keyboards.get_token_keyboard()
    await callback_query.message.answer(
        "*Выберите один из доступных вариантов:*",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN_V2,
    )


@router.callback_query(callbacks.Token.filter(F.action == callbacks.Action.add))
async def process_add_tokens(
        callback_query: CallbackQuery,
        callback_data: callbacks.Token,
):
    builder = InlineKeyboardBuilder()
    message = await callback_query.message.answer(
        f"Вы выбрали: *{callback_data.value} токенов*\n"
        f"Цена: *{callback_data.price}₽*\n\n"
        f"*⏳ Генерация ссылки на оплату, пожалуйста, подождите.. *",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN,
    )
    response, status = await api.create_payment(
        callback_query.from_user.id,
        callback_data.value,
        callback_data.price,
        message.message_id,
    )
    builder.button(text="💳 Оплатить", url=response["url"])
    builder.adjust(1)
    await message.edit_text(
        f"Вы выбрали: *{callback_data.value} токенов*\n"
        f"Цена: *{callback_data.price}₽*\n\n"
        f"*✅ Оплатите по кнопке ниже:*",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(callbacks.Subscribe.filter(F.action == callbacks.Action.get))
async def process_buy_subscription(
        callback_query: CallbackQuery,
        callback_data: callbacks.Subscribe,
):
    keyboard = await keyboards.get_subscription_keyboard()

    await callback_query.message.answer(
        f"*Выберите один из доступных вариантов:*\n",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN_V2,
    )
