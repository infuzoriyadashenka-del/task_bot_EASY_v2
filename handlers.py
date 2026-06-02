import re
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message

from database import (
    add_task,
    get_all_active_tasks,
    get_task,
    update_task_status,
    update_deadline,
    save_group,
    get_closed_tasks,
    get_active_tasks_by_executor,
    get_all_tasks_by_executor
)

router = Router()

UTC_OFFSET = 3


# =========================
# TIME HELPERS
# =========================

def now_msk():
    return datetime.utcnow() + timedelta(hours=UTC_OFFSET)


# Проверяет, прошёл ли дедлайн (для пометки просрочки).
# deadline хранится в виде строки "12.06.2026 18:00".
def is_overdue(deadline_str):
    try:
        dl = datetime.strptime(deadline_str, "%d.%m.%Y %H:%M")
        return now_msk() > dl
    except:
        return False


# =========================
# PARSER (task: ...)
# =========================

def parse_task(text: str):

    executor_match = re.search(r"@(\w+)", text)
    if not executor_match:
        return None, None, None

    executor = "@" + executor_match.group(1)
    text = text.replace(executor, "").strip()

    date = now_msk().date()
    time = "18:00"

    time_match = re.search(r"(\d{2}:\d{2})", text)
    if time_match:
        time = time_match.group(1)
        text = text.replace(time, "")

    date_match = re.search(r"(\d{2}\.\d{2}\.\d{4})", text)
    if date_match:
        date = datetime.strptime(date_match.group(1), "%d.%m.%Y").date()
        text = text.replace(date_match.group(1), "")

    dt = datetime.strptime(
        f"{date} {time}",
        "%Y-%m-%d %H:%M"
    )

    return text.strip(), executor, dt.strftime("%d.%m.%Y %H:%M")


# =========================
# CREATE TASK
# =========================

@router.message(F.text.startswith("задача:"))
async def create_task(message: Message):

    raw = message.text.replace("задача:", "").strip()

    task, executor, deadline = parse_task(raw)

    if not task:
        await message.answer("❌ Формат: задача: текст @user 12.06.2026 18:00")
        return

    await add_task(message.chat.id, task, executor, deadline)

    await message.answer(
        f"✅ Задача создана\n"
        f"📌 {task}\n"
        f"👤 {executor}\n"
        f"⏰ {deadline}"
    )


# =========================
# TASK LIST (с пометкой просрочки)
# =========================

@router.message(F.text == "/tasks")
async def tasks(message: Message):

    tasks = await get_all_active_tasks()

    if not tasks:
        await message.answer("📋 Активных задач нет 🎉")
        return

    text = "📋 Активные задачи:\n\n"

    for t in tasks:
        # t[0]=id, t[2]=task, t[3]=executor, t[4]=deadline
        mark = " 🔴 ПРОСРОЧЕНО" if is_overdue(t[4]) else ""
        text += f"#{t[0]} | {t[2]} | {t[3]} | {t[4]}{mark}\n"

    await message.answer(text)


# =========================
# НОВОЕ: ЗАДАЧИ КОНКРЕТНОГО ЧЕЛОВЕКА
# Использование: /my @username
# =========================

@router.message(F.text.startswith("/my"))
async def my_tasks(message: Message):

    executor_match = re.search(r"@(\w+)", message.text)
    if not executor_match:
        await message.answer("❌ Формат: /my @username")
        return

    executor = "@" + executor_match.group(1)

    tasks = await get_active_tasks_by_executor(message.chat.id, executor)

    if not tasks:
        await message.answer(f"📋 У {executor} нет активных задач 🎉")
        return

    text = f"📋 Активные задачи {executor}:\n\n"

    for t in tasks:
        mark = " 🔴 ПРОСРОЧЕНО" if is_overdue(t[4]) else ""
        text += f"#{t[0]} | {t[2]} | {t[4]}{mark}\n"

    await message.answer(text)


# =========================
# НОВОЕ: СТАТИСТИКА УЧАСТНИКА
# Использование: /stats @username
# =========================

@router.message(F.text.startswith("/stats"))
async def stats(message: Message):

    executor_match = re.search(r"@(\w+)", message.text)
    if not executor_match:
        await message.answer("❌ Формат: /stats @username")
        return

    executor = "@" + executor_match.group(1)

    all_tasks = await get_all_tasks_by_executor(message.chat.id, executor)

    if not all_tasks:
        await message.answer(f"📊 По {executor} задач пока нет")
        return

    done = 0
    cancelled = 0
    active = 0
    overdue_now = 0       # активные с прошедшим дедлайном
    done_late = 0         # сделанные после дедлайна

    for t in all_tasks:
        status = t[5]
        deadline = t[4]

        if status == "done":
            done += 1
            if is_overdue(deadline):
                done_late += 1
        elif status == "cancelled":
            cancelled += 1
        elif status == "active":
            active += 1
            if is_overdue(deadline):
                overdue_now += 1

    total = len(all_tasks)

    text = (
        f"📊 Статистика {executor}\n\n"
        f"📦 Всего задач: {total}\n"
        f"🟢 Активных: {active}\n"
        f"✅ Сделано: {done}\n"
        f"❌ Отменено: {cancelled}\n\n"
        f"🔴 Сейчас просрочено: {overdue_now}\n"
        f"⏱ Закрыто с опозданием: {done_late}"
    )

    await message.answer(text)


# =========================
# DONE TASK
# =========================

@router.message(F.text.startswith("/done"))
async def done(message: Message):

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("❌ Формат: /done 5")
        return

    task_id = int(parts[1])

    task = await get_task(task_id, message.chat.id)

    if not task:
        await message.answer("❌ Не найдено")
        return

    await update_task_status(task_id, "done")

    await message.answer(f"✅ Выполнено #{task_id}")


# =========================
# CANCEL TASK
# =========================

@router.message(F.text.startswith("/cancel"))
async def cancel(message: Message):

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("❌ Формат: /cancel 5")
        return

    task_id = int(parts[1])

    task = await get_task(task_id, message.chat.id)

    if not task:
        await message.answer("❌ Не найдено")
        return

    await update_task_status(task_id, "cancelled")

    await message.answer(f"❌ Отменено #{task_id}")


# =========================
# DEADLINE UPDATE
# =========================

@router.message(F.text.startswith("/deadline"))
async def deadline(message: Message):

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await message.answer("❌ Формат: /deadline 5 12.06.2026 18:00")
        return

    task_id = int(parts[1])
    new_deadline = parts[2]

    task = await get_task(task_id, message.chat.id)

    if not task:
        await message.answer("❌ Не найдено")
        return

    await update_deadline(task_id, new_deadline)

    await message.answer(f"⏰ Дедлайн обновлён #{task_id}")


# =========================
# CLOSED TASKS
# =========================

@router.message(F.text == "/closed")
async def closed(message: Message):

    tasks = await get_closed_tasks(message.chat.id)

    if not tasks:
        await message.answer("📦 Закрытых задач пока нет")
        return

    text = "📦 Закрытые задачи:\n\n"

    for t in tasks:
        text += f"#{t[0]} | {t[2]} | {t[3]} | {t[5]}\n"

    await message.answer(text)


# =========================
# REGISTER GROUP
# =========================
# ВАЖНО: этот хендлер ДОЛЖЕН быть В САМОМ КОНЦЕ файла,
# потому что @router.message() ловит ВСЕ сообщения.

@router.message()
async def register_group(message: Message):
    if message.chat.type in ("group", "supergroup"):
        await save_group(message.chat.id)
