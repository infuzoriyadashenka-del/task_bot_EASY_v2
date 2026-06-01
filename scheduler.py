import random
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import (
get_all_active_tasks,
mark_notification,
update_last_overdue_notice,
add_penalty,
get_groups
)

UTC_OFFSET = 3

scheduler = AsyncIOScheduler()
BOT = None

# =====================================

# TIME UTILS

# =====================================

def now_msk():
return datetime.utcnow() + timedelta(hours=UTC_OFFSET)

def parse_deadline(value: str):
return datetime.strptime(value, "%d.%m.%Y %H:%M")

# =====================================

# CORE CHECKER

# =====================================

async def check_tasks():

```
tasks = await get_all_active_tasks()
current_time = now_msk()

for task in tasks:

    task_id = task[0]
    chat_id = task[1]
    task_text = task[2]
    executor = task[3]
    deadline = task[4]

    notified_24h = task[6]
    notified_2h = task[7]
    last_notice = task[8]

    try:
        deadline_dt = parse_deadline(deadline)
    except:
        continue

    delta = deadline_dt - current_time
    seconds = delta.total_seconds()

    # =========================
    # 24 HOURS NOTIFICATION
    # =========================

    if 0 < seconds <= 86400 and not notified_24h:

        await BOT.send_message(
            chat_id,
            f"⏰ Напоминание\n\n"
            f"Задача #{task_id}\n\n"
            f"📌 {task_text}\n"
            f"👤 {executor}\n\n"
            f"До дедлайна остались сутки."
        )

        await mark_notification(task_id, "notified_24h")

    # =========================
    # 2 HOURS NOTIFICATION
    # =========================

    if 0 < seconds <= 7200 and not notified_2h:

        await BOT.send_message(
            chat_id,
            f"⚠️ Срочное напоминание\n\n"
            f"Задача #{task_id}\n\n"
            f"📌 {task_text}\n"
            f"👤 {executor}\n\n"
            f"До дедлайна осталось 2 часа."
        )

        await mark_notification(task_id, "notified_2h")

    # =========================
    # OVERDUE LOGIC
    # =========================

    if current_time > deadline_dt:

        should_send = False

        if not last_notice:
            should_send = True
        else:
            try:
                last_dt = datetime.strptime(
                    last_notice,
                    "%Y-%m-%d %H:%M:%S"
                )

                if (current_time - last_dt).total_seconds() >= 1800:
                    should_send = True
            except:
                should_send = True

        if should_send:

            await BOT.send_message(
                chat_id,
                f"🚨 ПРОСРОЧЕННАЯ ЗАДАЧА\n\n"
                f"#{task_id}\n\n"
                f"📌 {task_text}\n"
                f"👤 {executor}\n\n"
                f"Сдайте задачу."
            )

            if not last_notice:
                await add_penalty(chat_id, executor)

            await update_last_overdue_notice(
                task_id,
                current_time.strftime("%Y-%m-%d %H:%M:%S")
            )
```

# =====================================

# MORNING MESSAGE

# =====================================

async def morning_message():

```
names = ["Даша", "Вася", "Василиса", "Лизочек"]

poop = random.choice(names)
beauty = random.choice([n for n in names if n != poop])

groups = await get_groups()

if not groups:
    return

for g in groups:

    chat_id = g[0]

    await BOT.send_message(
        chat_id,
        f"Всем привет! ☀️\n\n"
        f"💩 Какашка дня — {poop}\n\n"
        f"💅 Красотка дня — {beauty}"
    )
```

# =====================================

# SETUP

# =====================================

def setup_scheduler(bot):

```
global BOT
BOT = bot

scheduler.add_job(
    check_tasks,
    "interval",
    minutes=1,
    id="check_tasks"
)

scheduler.add_job(
    morning_message,
    "cron",
    hour=10,
    minute=30,
    timezone="Europe/Moscow",
    id="morning_message"
)

scheduler.start()
```
