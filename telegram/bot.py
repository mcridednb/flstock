from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from redis import asyncio as redis

from settings import settings

bot = Bot(token=settings.telegram_bot_token)


async def on_startup(dispatcher: Dispatcher):
    await bot.set_webhook(
        f"{settings.base_webhook_url}{settings.webhook_path}",
        secret_token=settings.webhook_secret
    )


def main():
    from handlers.registration import router as registration_router
    from handlers.commands import router as commands_router
    from handlers.menu import router as menu_router
    from handlers.navigation import router as navigation_router
    from handlers.profile import router as profile_router
    from handlers.notifications import router as notifications_router
    from handlers.subscription import router as subscription_router
    from handlers.project import router as project_router

    redis_client = redis.StrictRedis(host=settings.redis_host, port=settings.redis_port, db=3)
    dp = Dispatcher(storage=RedisStorage(redis=redis_client))
    dp.include_routers(
        registration_router,
        commands_router,
        menu_router,
        notifications_router,
        profile_router,
        navigation_router,
        subscription_router,
        project_router,
    )
    dp.startup.register(on_startup)
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret,
    )
    webhook_requests_handler.register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host=settings.web_server_host, port=settings.web_server_port)


async def dev():
    from handlers.registration import router as registration_router
    from handlers.commands import router as commands_router
    from handlers.menu import router as menu_router
    from handlers.navigation import router as navigation_router
    from handlers.profile import router as profile_router
    from handlers.notifications import router as notifications_router
    from handlers.subscription import router as subscription_router
    from handlers.project import router as project_router

    dp = Dispatcher()
    dp.include_routers(
        registration_router,
        commands_router,
        menu_router,
        notifications_router,
        profile_router,
        navigation_router,
        subscription_router,
        project_router,
    )
    await bot.delete_webhook()
    await dp.start_polling(bot)


if __name__ == "__main__":
    # import asyncio
    # asyncio.run(dev())
    main()
