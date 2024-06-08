from aiogram import Router, F
from aiogram.types import CallbackQuery

import api
import callbacks

router = Router()


@router.callback_query(callbacks.Subscribe.filter(F.action == callbacks.Action.add))
async def process_add_subscription(
        callback_query: CallbackQuery,
        callback_data: callbacks.Subscribe,
):
    result, _ = await api.add_subscription(
        callback_query.from_user.id,
        callback_data.tokens,
        callback_data.value,
        callback_query.message.message_id,
    )
