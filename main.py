import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from handlers import router
from database import init_db
from scheduler import setup_scheduler


# =====================================
# CONFIG
# =====================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing")


# =====================================
# LOGGING
# =====================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# =====================================
# BOT INIT
# =====================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =====================================
# STARTUP
# =====================================

async def startup():
    logging.info("init db...")
    await init_db()

    logging.info("router...")
    dp.include_router(router)

    logging.info("scheduler...")
    setup_scheduler(bot)

    logging.info("cleanup webhook + updates...")

    # важно: убираем webhook и старые апдейты (анти-conflict)
    await bot.delete_webhook(drop_pending_updates=True)

    logging.info("start polling...")


# =====================================
# MAIN LOOP
# =====================================

async def main():
    await startup()

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


# =====================================
# ENTRY POINT
# =====================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped")
