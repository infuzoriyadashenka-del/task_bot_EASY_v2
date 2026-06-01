import aiosqlite

DB_NAME = "tasks.db"


# ================= INIT =================

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            text TEXT,
            executor TEXT,
            deadline TEXT,
            status TEXT DEFAULT 'active',
            notified_24h INTEGER DEFAULT 0,
            notified_2h INTEGER DEFAULT 0,
            last_overdue TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            chat_id INTEGER PRIMARY KEY
        )
        """)

        await db.commit()


# ================= TASKS =================

async def add_task(chat_id, text, executor, deadline):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT INTO tasks(chat_id, text, executor, deadline)
        VALUES (?, ?, ?, ?)
        """, (chat_id, text, executor, deadline))
        await db.commit()


async def get_all_active_tasks():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT * FROM tasks WHERE status='active'
        """)
        return await cursor.fetchall()


async def get_task(task_id, chat_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT * FROM tasks WHERE id=? AND chat_id=?
        """, (task_id, chat_id))
        return await cursor.fetchone()


async def update_task_status(task_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        UPDATE tasks SET status=? WHERE id=?
        """, (status, task_id))
        await db.commit()


async def update_deadline(task_id, deadline):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        UPDATE tasks SET deadline=? WHERE id=?
        """, (deadline, task_id))
        await db.commit()


async def mark_notification(task_id, field):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(f"""
        UPDATE tasks SET {field}=1 WHERE id=?
        """, (task_id,))
        await db.commit()


async def update_last_overdue_notice(task_id, time):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        UPDATE tasks SET last_overdue=? WHERE id=?
        """, (time, task_id))
        await db.commit()


# ================= GROUPS =================

async def save_group(chat_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT OR IGNORE INTO groups(chat_id)
        VALUES(?)
        """, (chat_id,))
        await db.commit()


async def get_groups():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT chat_id FROM groups")
        return await cursor.fetchall()
