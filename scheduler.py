import random
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import (
get_all_active_tasks,
mark_notification,
update_last_overdue_notice,
add_penalty
)

UTC_OFFSET = 3

scheduler = AsyncIOScheduler()

BOT = None

def now_msk():
return datetime.utcnow() + timedelta(hours=UTC_OFFSET)

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
        deadline_dt = datetime.strptime(
            deadline,
            "%d.%m.%Y %H:%M"
        )
    except:
        continue

    delta = deadline_dt - current_time

    # За 24 часа

    if (
        delta.total_seconds() <= 86400
        and delta.total_seconds() > 86340
        and not notified_24h
    ):

        await BOT.send_message(
            chat_id,
            f"⏰ Напоминание\n\n"
            f"Задача #{task_id}\n\n"
            f"📌 {task_text}\n"
            f"👤 {executor}\n\n"
            f"До дедлайна остались сутки."
        )

        await mark_notification(
            task_id,
            "notified_24h"
        )

    # За 2 часа

    if (
        delta.total_seconds() <= 7200
        and delta.total_seconds() > 7140
        and not notified_2h
    ):

        await BOT.send_message(
            chat_id,
            f"⚠️ Срочное напоминание\n\n"
            f"Задача #{task_id}\n\n"
            f"📌 {task_text}\n"
            f"👤 {executor}\n\n"
            f"До дедлайна осталось 2 часа."
        )

        await mark_notification(
            task_id,
            "notified_2h"
        )

    # Просрочка

    if current_time > deadline_dt:

        send_overdue = False

        if not last_notice:
            send_overdue = True

        else:

            try:
                notice_time = datetime.strptime(
                    last_notice,
                    "%Y-%m-%d %H:%M:%S"
                )

                if (
                    current_time - notice_time
                ).total_seconds() >= 1800:
                    send_overdue = True

            except:
                send_overdue = True

        if send_overdue:

            await BOT.send_message(
                chat_id,
                f"🚨 ПРОСРОЧЕННАЯ ЗАДАЧА\n\n"
                f"Задача #{task_id}\n\n"
                f"📌 {task_text}\n"
                f"👤 {executor}\n\n"
                f"Сдайте задачу."
            )

            if not last_notice:
                await add_penalty(
                    chat_id,
                    executor
                )

            await update_last_overdue_notice(
                task_id,
                current_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
```

async def morning_message():

```
names = [
    "Даша",
    "Вася",
    "Василиса",
    "Лизочек"
]

poop = random.choice(names)

beauty = random.choice(
    [x for x in names if x != poop]
)

tasks = await get_all_active_tasks()

if not tasks:
    return

chat_id = tasks[0][1]

await BOT.send_message(
    chat_id,
    f"Всем привет! ☀️\n\n"
    f"💩 Какашка дня — {poop}\n\n"
    f"💅 Красотка дня — {beauty}"
)
```

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

