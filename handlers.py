import re
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message

from database import (
add_task,
get_active_tasks,
get_task,
update_task_status,
update_deadline,
get_closed_tasks,
get_rating,
get_stats,
save_group
)

router = Router()

UTC_OFFSET = 3

# =====================================

# TIME PARSER

# =====================================

def now_msk():
return datetime.utcnow() + timedelta(hours=UTC_OFFSET)

def parse_datetime(text: str):

```
text = text.lower().strip()
base = now_msk()

if "сегодня" in text:
    date = base.date()
    text = text.replace("сегодня", "").strip()

elif "завтра" in text:
    date = (base + timedelta(days=1)).date()
    text = text.replace("завтра", "").strip()

else:
    match = re.search(r"(\d{2}\.\d{2}\.\d{4})", text)
    if match:
        date = datetime.strptime(match.group(1), "%d.%m.%Y").date()
        text = text.replace(match.group(1), "").strip()
    else:
        return None, None

time_match = re.search(r"(\d{2}:\d{2})", text)
if time_match:
    time_part = time_match.group(1)
    text = text.replace(time_part, "").strip()
else:
    time_part = "18:00"

dt = datetime.strptime(
    f"{date} {time_part}",
    "%Y-%m-%d %H:%M"
)

return text.strip(), dt.strftime("%d.%m.%Y %H:%M")
```

# =====================================

# GROUP REGISTRATION

# =====================================

@router.message()
async def register_group(message: Message):
if message.chat.type in ["group", "supergroup"]:
await save_group(message.chat.id)

# =====================================

# CREATE TASK

# =====================================

@router.message(F.text.lower().startswith("задача:"))
async def create_task(message: Message):

```
text = message.text.replace("задача:", "").strip()

executor_match = re.search(r"@(\w+)", text)

if not executor_match:
    await message.answer("❌ Укажи исполнителя через @username")
    return

executor = "@" + executor_match.group(1)

clean_text = text.replace(executor, "").strip()

task_text, deadline = parse_datetime(clean_text)

if not task_text or not deadline:
    await message.answer("❌ Неверный формат даты. Пример: сегодня 18:00")
    return

await add_task(
    message.chat.id,
    task_text,
    executor,
    deadline
)

await message.answer(
    f"✅ Задача создана\n\n"
    f"📌 {task_text}\n"
    f"👤 {executor}\n"
    f"⏰ {deadline}"
)
```

# =====================================

# TASK LIST

# =====================================

@router.message(F.text == "/tasks")
async def tasks(message: Message):

```
tasks = await get_active_tasks(message.chat.id)

if not tasks:
    await message.answer("Активных задач нет")
    return

text = "📋 Активные задачи:\n\n"

for t in tasks:
    text += f"#{t[0]} {t[2]} | {t[3]} | {t[4]}\n"

await message.answer(text)
```

# =====================================

# TASK DONE

# =====================================

@router.message(F.text.startswith("/done"))
async def done(message: Message):

```
task_id = int(message.text.split()[1])

task = await get_task(task_id, message.chat.id)

if not task:
    await message.answer("❌ Задача не найдена")
    return

await update_task_status(task_id, "done")

await message.answer(f"✅ Задача #{task_id} выполнена")
```

# =====================================

# CANCEL TASK

# =====================================

@router.message(F.text.startswith("/cancel"))
async def cancel(message: Message):

```
task_id = int(message.text.split()[1])

task = await get_task(task_id, message.chat.id)

if not task:
    await message.answer("❌ Задача не найдена")
    return

await update_task_status(task_id, "cancelled")

await message.answer(f"❌ Задача #{task_id} отменена")
```

# =====================================

# DEADLINE CHANGE

# =====================================

@router.message(F.text.startswith("/deadline"))
async def deadline(message: Message):

```
parts = message.text.split(maxsplit=2)

task_id = int(parts[1])
new_deadline = parts[2]

task = await get_task(task_id, message.chat.id)

if not task:
    await message.answer("❌ Задача не найдена")
    return

await update_deadline(task_id, new_deadline)

await message.answer(f"⏰ Дедлайн обновлён для #{task_id}")
```

# =====================================

# CLOSED TASKS

# =====================================

@router.message(F.text == "/closed")
async def closed(message: Message):

```
tasks = await get_closed_tasks(message.chat.id)

text = "📦 Закрытые задачи:\n\n"

for t in tasks:
    text += f"#{t[0]} {t[2]} | {t[3]} | {t[5]}\n"

await message.answer(text)
```

# =====================================

# RATING

# =====================================

@router.message(F.text == "/rating")
async def rating(message: Message):

```
data = await get_rating(message.chat.id)

text = "🏆 Рейтинг:\n\n"

for row in data:
    text += f"{row[0]} — {row[1]} задач\n"

await message.answer(text)
```

# =====================================

# STATS

# =====================================

@router.message(F.text == "/stats")
async def stats(message: Message):

```
data = await get_stats(message.chat.id)

text = "📊 Статистика:\n\n"

for row in data:
    text += f"{row[0]} — ✅ {row[1]} | ⏳ {row[2]}\n"

await message.answer(text)
```

# =====================================

# ANALYTICS (simple)

# =====================================

@router.message(F.text == "/analytics")
async def analytics(message: Message):

```
data = await get_stats(message.chat.id)

total = 0
done = 0

for row in data:
    done += row[1]
    total += row[1] + row[2]

percent = (done / total * 100) if total else 0

await message.answer(
    f"📈 Аналитика\n\n"
    f"Всего задач: {total}\n"
    f"Выполнено: {done}\n"
    f"Прогресс: {percent:.1f}%"
)
```

