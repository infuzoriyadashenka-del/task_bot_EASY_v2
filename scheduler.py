import random
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import (
    get_all_active_tasks,
    mark_notification,
    update_last_overdue_notice,
    get_groups
)

UTC_OFFSET = 3

scheduler = AsyncIOScheduler()
BOT = None


def now():
    return datetime.utcnow() + timedelta(hours=UTC_OFFSET)


def parse_dt(s):
    return datetime.strptime(s, "%d.%m.%Y %H:%M")


# ================= TASK CHECK =================

async def check_tasks():

    tasks = await get_all_active_tasks()
    current = now()

    for t in tasks:

        task_id, chat_id, text, executor, deadline, status, n24, n2, last = t

        try:
            dl = parse_dt(deadline)
        except:
            continue

        diff = (dl - current).total_seconds()

        # 24h
        if 0 < diff <= 86400 and not n24:
            await BOT.send_message(chat_id, f"⏰ 24ч: {text}")
            await mark_notification(task_id, "notified_24h")

        # 2h
        if 0 < diff <= 7200 and not n2:
            await BOT.send_message(chat_id, f"⚠️ 2ч: {text}")
            await mark_notification(task_id, "notified_2h")

        # overdue
        if current > dl:

            if not last or (current - datetime.strptime(last, "%Y-%m-%d %H:%M:%S")).seconds >= 1800:
                await BOT.send_message(chat_id, f"🚨 ПРОСРОЧКА: {text}")

                await update_last_overdue_notice(
                    task_id,
                    current.strftime("%Y-%m-%d %H:%M:%S")
                )


# ================= MORNING =================

async def morning():

    names = ["Даша", "Вася", "Василиса", "Лизочек"]

    poop = random.choice(names)
    beauty = random.choice([n for n in names if n != poop])

    groups = await get_groups()

    for g in groups:
        await BOT.send_message(
            g[0],
            f"Всем привет! ☀️\n💩 {poop}\n💅 {beauty}"
        )


def setup_scheduler(bot):

    global BOT
    BOT = bot

    scheduler.add_job(check_tasks, "interval", minutes=1)
    scheduler.add_job(morning, "cron", hour=10, minute=30, timezone="Europe/Moscow")

    scheduler.start()
