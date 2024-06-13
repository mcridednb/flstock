from aiogram.utils.keyboard import InlineKeyboardBuilder

import api
import callbacks
from states import Registration


async def get_subscriptions_keyboard(chat_id, category_code):
    subcategories, _ = await api.subcategories_list(chat_id, category_code)

    builder = InlineKeyboardBuilder()
    for subcategory in subcategories:
        title = subcategory["title"]
        if subcategory["is_subscribed"]:
            title = f"✅ {title}"
        builder.button(
            text=title,
            callback_data=callbacks.Subcategory(
                action=callbacks.Action.set,
                code=subcategory["code"]
            ),
        )

    builder.button(
        text="⬅️ Назад",
        callback_data="back",
    )

    builder.adjust(1)
    return builder.as_markup()


async def get_categories_keyboard(message, state):
    categories, _ = await api.categories_list(message)

    builder = InlineKeyboardBuilder()
    for category in categories:
        title = category["title"]
        if category["is_subscribed"]:
            title = f"✅ {title}"
        builder.button(
            text=title,
            callback_data=callbacks.Category(
                action=callbacks.Action.set,
                code=category["code"]
            ),
        )

    state = await state.get_state()
    if state in [Registration.category, Registration.subcategory]:
        builder.button(text="Далее ➡️", callback_data="next")
    else:
        builder.button(text="⬅️ Назад", callback_data="notifications")

    builder.adjust(1)
    return builder.as_markup()


async def get_sources_keyboard(message, state):
    sources, _ = await api.sources_list(message)
    builder = InlineKeyboardBuilder()
    for source in sources:
        title = source["title"]
        if source["is_subscribed"]:
            title = f"✅ {title}"
        builder.button(
            text=title,
            callback_data=callbacks.Source(
                action=callbacks.Action.set,
                code=source["code"],
            )
        )

    state = await state.get_state()
    if state in [Registration.source]:
        builder.button(
            text="Далее ➡️",
            callback_data="next",
        )
    else:
        builder.button(
            text="⬅️ Назад",
            callback_data="notifications",
        )

    builder.adjust(1)
    return builder.as_markup()


async def get_close_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Закрыть",
        callback_data="close",
    )
    builder.adjust(1)
    return builder.as_markup()


async def get_cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🚫 Отмена",
        callback_data="close",
    )
    builder.adjust(1)
    return builder.as_markup()


async def get_menu_keyboard(message_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Редактировать профиль", callback_data="profile")
    builder.button(text="🔔 Редактировать уведомления", callback_data="notifications")
    builder.button(text="👥 Пригласить друзей", callback_data="referral")
    # builder.button(text="📝 Задания", callback_data="tasks")
    builder.button(
        text="🪙 Пополнить токены",
        callback_data=callbacks.Token(
            action=callbacks.Action.get,
        ),
    )
    builder.button(
        text="💳 Оформить подписку",
        callback_data=callbacks.Subscribe(
            action=callbacks.Action.get,
            message_id=message_id
        ),
    )
    builder.button(text="❤️ Поддержать проект", callback_data="donate")
    builder.button(text="🗣 Написать в поддержку", callback_data="support")
    builder.button(text="❌ Закрыть", callback_data="close")
    builder.adjust(1)
    return builder.as_markup()


async def get_balance_keyboard(message_id):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🪙 Пополнить токены",
        callback_data=callbacks.Token(
            action=callbacks.Action.get,
        ),
    )
    builder.button(
        text="💳 Оформить подписку",
        callback_data=callbacks.Subscribe(
            action=callbacks.Action.get,
            message_id=message_id
        ),
    )
    builder.button(text="❤️ Поддержать проект", callback_data="donate")
    builder.button(text="❌ Закрыть", callback_data="close")
    builder.adjust(1)
    return builder.as_markup()


async def get_notifications_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Редактировать источники", callback_data="sources")
    builder.button(text="📝 Редактировать категории", callback_data="categories")
    builder.button(text="🔑 Ключевые слова", callback_data="change_keywords")
    builder.button(text="⛔️ Минус слова", callback_data="change_stop_words")
    builder.button(text="🫰 Минимальная сумма", callback_data="change_min_price")
    builder.button(text="⬅️ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


async def get_change_profile_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Имя", callback_data="change_name")
    builder.button(text="🛠️ Навыки", callback_data="change_skills")
    builder.button(text="📝 О себе", callback_data="change_summary")
    builder.button(text="💼 Опыт", callback_data="change_experience")
    builder.button(text="⏰ Ставка в час", callback_data="change_hourly_rate")
    builder.button(text="⬅️ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


async def get_token_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🪙 40 токенов — 190₽",  # 4,75
        callback_data=callbacks.Token(
            action=callbacks.Action.add,
            price=190,
            value=40,
        ),
    )
    builder.button(
        text="💰 200 токенов — 740₽",  # 3,7
        callback_data=callbacks.Token(
            action=callbacks.Action.add,
            price=740,
            value=200,
        ),
    )
    builder.button(
        text="💎 400 токенов — 1190₽",  # 3
        callback_data=callbacks.Token(
            action=callbacks.Action.add,
            price=1190,
            value=400,
        ),
    )
    builder.adjust(1)
    return builder.as_markup()


async def get_subscription_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="👍 1 месяц — 35 токенов",  # 35
        callback_data=callbacks.Subscribe(
            action=callbacks.Action.add,
            tokens=35,
            value=30,
        ),
    )
    builder.button(
        text="💪 3 месяца — 90 токенов",  # 30
        callback_data=callbacks.Subscribe(
            action=callbacks.Action.add,
            tokens=90,
            value=90,
        ),
    )
    builder.button(
        text="🚀 6 месяцев — 150 токенов",  # 25
        callback_data=callbacks.Subscribe(
            action=callbacks.Action.add,
            tokens=150,
            value=180,
        ),
    )
    builder.adjust(1)
    return builder.as_markup()


async def get_tasks_keyboard(message, state):
    tasks, _ = await api.tasks_list(message)
    builder = InlineKeyboardBuilder()
    for task in tasks:
        title = task["title"]
        if task["done"]:
            title = f"✅ {title}"
        builder.button(
            text=title,
            callback_data=callbacks.Task(
                action=callbacks.Action.set,
                code=source["code"],
            )
        )

    state = await state.get_state()
    if state in [Registration.source]:
        builder.button(
            text="Далее ➡️",
            callback_data="next",
        )
    else:
        builder.button(
            text="⬅️ Назад",
            callback_data="notifications",
        )

    builder.adjust(1)
    return builder.as_markup()