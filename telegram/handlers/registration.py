from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

import api
import callbacks
import keyboards
from handlers.menu import get_menu_data
from states import Registration

router = Router()


@router.message(Registration.email)
async def process_email(message: Message, state: FSMContext):
    _, status = await api.user_patch(message, "email", message.text)

    if status == 400:
        await message.answer(
            "⚠️ *Что-то пошло не так. Убедитесь, что вы ввели верный email.*\n\n"
            "✏️ *Пожалуйста, введите ваш адрес электронной почты:*",
            parse_mode=ParseMode.MARKDOWN,
        )
        await state.set_state(Registration.email)
        return
    else:
        await state.clear()
        await process_start(message, state)


@router.message(CommandStart(deep_link=True, deep_link_encoded=True))
async def process_start_deep(message: Message, state: FSMContext, command: CommandObject):
    referrer = command.args
    await process_start(message, state, referrer)


@router.message(CommandStart())
async def process_start(message: Message, state: FSMContext, referrer=None):
    user_detail, status = await api.user_detail(message.from_user.id)
    if status == 404 or not user_detail["registration_completed"]:
        response, status = await api.user_create(message, referrer)
        # if not user_detail.get("email"):
        #     await message.answer(
        #         "👋 *Добро пожаловать!*\n\n"
        #         "✏️ *Пожалуйста, введите ваш адрес электронной почты:*",
        #         parse_mode=ParseMode.MARKDOWN,
        #     )
        #     await state.set_state(Registration.email)
        #     return

        await state.set_state(Registration.source)
        keyboard = await keyboards.get_sources_keyboard(message, state)
        await message.answer(
            "👋 *Добро пожаловать!*\n\n"
            "⚙️ *Настройка вашего бота...*\n\n"
            "🌐 Шаг 1 из 2: Выбор источников\n\n"
            "*Пожалуйста, выберите сайты, из которых вы хотите получать уведомления:*",
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


@router.callback_query(Registration.source, callbacks.Source.filter(F.action == callbacks.Action.set))
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


@router.callback_query(Registration.source, lambda call: call.data == "next")
async def process_next_1(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Registration.category)
    keyboard = await keyboards.get_categories_keyboard(callback_query, state)
    await callback_query.message.edit_text(
        "⚙️ *Настройка вашего бота...*\n\n"
        "📝 Шаг 2 из 2: Выбор категорий\n\n"
        "*Теперь, выберите категории, по которым хотите получать уведомления:*",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(Registration.category, callbacks.Category.filter(F.action == callbacks.Action.set))
async def process_category(
        callback_query: CallbackQuery,
        callback_data: callbacks.Category,
        state: FSMContext
) -> None:
    await state.set_state(Registration.subcategory)
    await state.set_data({
        "category": callback_data.code,
    })
    keyboard = await keyboards.get_subscriptions_keyboard(callback_query.from_user.id, callback_data.code)
    if len(keyboard.inline_keyboard) == 1:
        await callback_query.message.edit_text(
            "*Выбранная категория сейчас в разработке.\n"
            "Пожалуйста, выберите другую категорию.*",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await callback_query.message.edit_text(
            "⚙️ *Настройка вашего бота...*\n\n"
            "📝 Шаг 2 из 2: Выбор категорий\n\n"
            "*Теперь, выберите категории, по которым хотите получать уведомления:*",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )


@router.callback_query(Registration.category, lambda call: call.data == "next")
async def process_next_2(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback_query.message.edit_text(
        "🎉 *Поздравляем, вы успешно настроили бота!*\n\n"
        "💡 Вы всегда можете изменить свои предпочтения в настройках.\n\n"
        "📋 *Меню бота:* /menu\n\n",
        reply_markup=await keyboards.get_close_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
    )
    await api.registration_success(callback_query)


@router.callback_query(Registration.subcategory, lambda call: call.data == "back")
async def process_back(callback_query: CallbackQuery, state: FSMContext) -> None:
    keyboard = await keyboards.get_categories_keyboard(callback_query, state)

    await state.set_state(Registration.category)
    await callback_query.message.edit_text(
        "⚙️ *Настройка вашего бота...*\n\n"
        "📝 Шаг 2 из 2: Выбор категорий\n\n"
        "*Теперь, выберите категории, по которым хотите получать уведомления:*",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )
