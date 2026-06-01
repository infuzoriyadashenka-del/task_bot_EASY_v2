import re
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message

from database import add_task, save_group

router = Router()


def now():
    return datetime.utcnow() + timedelta(hours=3)


def parse(text):

    user = re.search(r"@(\w+)", text)
    if not user:
        return None, None, None

    executor = "@" + user.group(1)
    text = text.replace(executor, "")

    date = now().date()
    time = "18:00"

    t = re.search(r"(\d{2}:\d{2})", text)
    if t:
        time = t.group(1)
        text = text.replace(time, "")

    d = re.search(r"(\d{2}\.\d{2}\.\d{4})", text)
    if d:
        date = datetime.strptime(d.group(1), "%d.%m.%Y").date()
        text = text.replace(d.group(1), "")

    dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

    return text.strip(), executor, dt.strftime("%d.%m.%Y %H:%M")


@router.message()
async def register(message: Message):
    if message.chat.type in ("group", "supergroup"):
        await save_group(message.chat.id)


@router.message(F.text.startswith("задача:"))
async def create(message: Message):

    text = message.text.replace("задача:", "").strip()

    task, executor, deadline = parse(text)

    if not task:
        await message.answer("❌ Ошибка формата")
        return

    await add_task(message.chat.id, task, executor, deadline)

    await message.answer(f"✅ Создано: {task}")
