import asyncio
import logging
import os
import time

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from handlers import router
from database import init_db
from scheduler import setup_scheduler


# =========================
# ENV
# =========================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing")


# =========================
# CLEAN LOGGING (PRO MODE)
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("aiogram").setLevel(logging.INFO)


# =========================
# BOT
# =========================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


START_TIME = time.time()


# =========================
# STARTUP
# =========================

async def startup():

    await init_db()

    dp.include_router(router)

    setup_scheduler(bot)

    await bot.delete_webhook(drop_pending_updates=True)


# =========================
# MAIN LOOP
# =========================

async def main():

    await startup()

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


# =========================
# ENTRY
# =========================

if __name__ == "__main__":
    asyncio.run(main())
