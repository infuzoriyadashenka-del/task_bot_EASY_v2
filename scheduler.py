import random
import logging
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

# Список для утренней рубрики (💩/💅)
NAMES = ["Даша", "Вася", "Василиса", "Игорь", "ДашаШ"]

# Отдельный список для ежечасного шуточного вопроса
HOURLY_NAMES = ["@igor_easyagency Игорь", "@igor_easyagency Игорек"]


# =========================
# TIME
# =========================

def now_msk():
    return datetime.utcnow() + timedelta(hours=UTC_OFFSET)


def parse_dt(dt_str):
    return datetime.strptime(dt_str, "%d.%m.%Y %H:%M")


# Проверяет, прошёл ли дедлайн (для пометки просрочки в списке задач)
def is_overdue(deadline_str):
    try:
        dl = parse_dt(deadline_str)
        return now_msk() > dl
    except:
        return False


# =========================
# TASK CHECKER
# =========================

async def check_tasks():

    tasks = await get_all_active_tasks()
    now = now_msk()

    for t in tasks:

        task_id, chat_id, text, executor, deadline, status, n24, n2, last = t

        try:
            dl = parse_dt(deadline)
        except:
            continue

        diff = (dl - now).total_seconds()

        # 24h reminder — с тегом исполнителя
        if 0 < diff <= 86400 and not n24:
            await BOT.send_message(
                chat_id,
                f"⏰ 24ч до дедлайна:\n{text}\n👤 {executor}"
            )
            await mark_notification(task_id, "notified_24h")

        # 2h reminder — с тегом исполнителя
        if 0 < diff <= 7200 and not n2:
            await BOT.send_message(
                chat_id,
                f"⚠️ 2ч осталось:\n{text}\n👤 {executor}"
            )
            await mark_notification(task_id, "notified_2h")

        # overdue spam (каждые 30 минут)
        if now > dl:

            if not last:
                last_time = None
            else:
                try:
                    last_time = datetime.strptime(last, "%Y-%m-%d %H:%M:%S")
                except:
                    last_time = None

            if (not last_time) or (now - last_time).total_seconds() >= 1800:

                await BOT.send_message(
                    chat_id,
                    f"🚨 ПРОСРОЧКА:\n{text}\n👤 {executor}"
                )

                await update_last_overdue_notice(
                    task_id,
                    now.strftime("%Y-%m-%d %H:%M:%S")
                )


# =========================
# MORNING MESSAGE
# =========================

async def morning_message():

    poop = random.choice(NAMES)
    beauty = random.choice([n for n in NAMES if n != poop])

    groups = await get_groups()

    for g in groups:
        await BOT.send_message(
            g[0],
            f"Всем привет! ☀️\n💩 {poop}\n💅 {beauty}"
        )


# =========================
# ЕЖЕДНЕВНЫЙ СПИСОК АКТИВНЫХ ЗАДАЧ (10:30)
# =========================

async def daily_task_list():

    groups = await get_groups()

    for g in groups:

        chat_id = g[0]

        all_tasks = await get_all_active_tasks()
        tasks = [t for t in all_tasks if t[1] == chat_id]

        if not tasks:
            text = "📋 Активных задач нет 🎉"
        else:
            text = "📋 Активные задачи на сегодня:\n\n"
            for t in tasks:
                mark = " 🔴 ПРОСРОЧЕНО" if is_overdue(t[4]) else ""
                text += f"#{t[0]} | {t[2]} | {t[3]} | {t[4]}{mark}\n"

        await BOT.send_message(chat_id, text)


# =========================
# НОВОЕ: ЕЖЕЧАСНЫЙ ШУТОЧНЫЙ ВОПРОС
# =========================
# Раз в час случайно выбирается один человек из списка HOURLY_NAMES
# и случайно один из двух вопросов. Никто не выбирается специально —
# выбор полностью случайный по всем участникам.

QUESTIONS = ["ты куришь?", "ты спишь?"]

async def hourly_question():

    person = random.choice(HOURLY_NAMES)
    question = random.choice(QUESTIONS)

    groups = await get_groups()

    for g in groups:
        await BOT.send_message(
            g[0],
            f"🤔 {person}, {question}"
        )


# =========================
# START SCHEDULER
# =========================

def setup_scheduler(bot):

    global BOT
    BOT = bot

    scheduler.add_job(check_tasks, "interval", minutes=1)
    scheduler.add_job(morning_message, "cron", hour=10, minute=30, timezone="Europe/Moscow")
    scheduler.add_job(daily_task_list, "cron", hour=10, minute=30, timezone="Europe/Moscow")
    scheduler.add_job(hourly_question, "interval", hours=1)

    scheduler.start()

    logging.info("Scheduler started cleanly")
