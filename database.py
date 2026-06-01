import aiosqlite

DB_NAME = "tasks.db"

# =====================================

# INIT DATABASE

# =====================================

async def init_db():
async with aiosqlite.connect(DB_NAME) as db:

```
    await db.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        task_text TEXT NOT NULL,
        executor TEXT NOT NULL,
        deadline TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        notified_24h INTEGER DEFAULT 0,
        notified_2h INTEGER DEFAULT 0,
        last_overdue_notice TEXT
    )
    """)

    await db.execute("""
    CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        username TEXT NOT NULL
    )
    """)

    await db.execute("""
    CREATE TABLE IF NOT EXISTS penalties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        executor TEXT NOT NULL,
        points INTEGER DEFAULT 0
    )
    """)

    await db.execute("""
    CREATE TABLE IF NOT EXISTS streaks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        executor TEXT NOT NULL,
        streak INTEGER DEFAULT 0,
        max_streak INTEGER DEFAULT 0
    )
    """)

    await db.commit()
```

# =====================================

# TASKS

# =====================================

async def add_task(chat_id, task_text, executor, deadline):
async with aiosqlite.connect(DB_NAME) as db:
await db.execute(
"""
INSERT INTO tasks
(chat_id, task_text, executor, deadline)
VALUES (?, ?, ?, ?)
""",
(chat_id, task_text, executor, deadline)
)
await db.commit()

async def get_task(task_id, chat_id):
async with aiosqlite.connect(DB_NAME) as db:
cursor = await db.execute(
"""
SELECT * FROM tasks
WHERE id=? AND chat_id=?
""",
(task_id, chat_id)
)
return await cursor.fetchone()

async def get_all_tasks():
async with aiosqlite.connect(DB_NAME) as db:
cursor = await db.execute(
"SELECT * FROM tasks"
)
return await cursor.fetchall()

async def get_all_active_tasks():
async with aiosqlite.connect(DB_NAME) as db:
cursor = await db.execute(
"""
SELECT * FROM tasks
WHERE status='active'
"""
)
return await cursor.fetchall()

async def get_active_tasks(chat_id):
async with aiosqlite.connect(DB_NAME) as db:
cursor = await db.execute(
"""
SELECT * FROM tasks
WHERE chat_id=?
AND status='active'
ORDER BY id DESC
""",
(chat_id,)
)
return await cursor.fetchall()

async def get_closed_tasks(chat_id):
async with aiosqlite.connect(DB_NAME) as db:
cursor = await db.execute(
"""
SELECT * FROM tasks
WHERE chat_id=?
AND status != 'active'
ORDER BY id DESC
""",
(chat_id,)
)
return await cursor.fetchall()

async def get_tasks_by_executor(chat_id, executor):
async with aiosqlite.connect(DB_NAME) as db:
cursor = await db.execute(
"""
SELECT * FROM tasks
WHERE chat_id=? AND executor=?
ORDER BY id DESC
""",
(chat_id, executor)
)
return await cursor.fetchall()

async def get_last_tasks(chat_id, limit=10):
async with aiosqlite.connect(DB_NAME) as db:
cursor = await db.execute(
"""
SELECT * FROM tasks
WHERE chat_id=?
ORDER BY id DESC
LIMIT ?
""",
(chat_id, limit)
)
return await cursor.fetchall()

# =====================================

# UPDATE TASKS

# =====================================

async def update_task_status(task_id, status):
async with aiosqlite.connect(DB_NAME) as db:
await db.execute(
"""
UPDATE tasks
SET status=?
WHERE id=?
""",
(status, task_id)
)
await db.commit()

async def update_deadline(task_id, deadline):
async with aiosqlite.connect(DB_NAME) as db:
await db.execute(
"""
UPDATE tasks
SET deadline=?
WHERE id=?
""",
(deadline, task_id)
)
await db.commit()

async def mark_notification(task_id, column):
async with aiosqlite.connect(DB_NAME) as db:
await db.execute(
f"""
UPDATE tasks
SET {column}=1
WHERE id=?
""",
(task_id,)
)
await db.commit()

async def update_last_overdue_notice(task_id, value):
async with aiosqlite.connect(DB_NAME) as db:
await db.execute(
"""
UPDATE tasks
SET last_overdue_notice=?
WHERE id=?
""",
(value, task_id)
)
await db.commit()

# =====================================

# PARTICIPANTS

# =====================================

async def add_participant(chat_id, username):
async with aiosqlite.connect(DB_NAME) as db:

```
    cursor = await db.execute(
        """
        SELECT id
        FROM participants
        WHERE chat_id=? AND username=?
        """,
        (chat_id, username)
    )

    exists = await cursor.fetchone()

    if not exists:
        await db.execute(
            """
            INSERT INTO participants
            (chat_id, username)
            VALUES (?, ?)
            """,
            (chat_id, username)
        )
        await db.commit()
```

async def get_participants(chat_id):
async with aiosqlite.connect(DB_NAME) as db:
cursor = await db.execute(
"""
SELECT username
FROM participants
WHERE chat_id=?
""",
(chat_id,)
)
return await cursor.fetchall()

# =====================================

# PENALTIES

# =====================================

async def add_penalty(chat_id, executor):
async with aiosqlite.connect(DB_NAME) as db:

```
    cursor = await db.execute(
        """
        SELECT id, points
        FROM penalties
        WHERE chat_id=? AND executor=?
        """,
        (chat_id, executor)
    )

    row = await cursor.fetchone()

    if row:
        await db.execute(
            """
            UPDATE penalties
            SET points = points + 1
            WHERE id=?
            """,
            (row[0],)
        )
    else:
        await db.execute(
            """
            INSERT INTO penalties
            (chat_id, executor, points)
            VALUES (?, ?, 1)
            """,
            (chat_id, executor)
        )

    await db.commit()
```

async def get_penalties(chat_id):
async with aiosqlite.connect(DB_NAME) as db:
cursor = await db.execute(
"""
SELECT executor, points
FROM penalties
WHERE chat_id=?
ORDER BY points DESC
""",
(chat_id,)
)
return await cursor.fetchall()

# =====================================

# STREAKS

# =====================================

async def update_streak(chat_id, executor, success=True):
async with aiosqlite.connect(DB_NAME) as db:

```
    cursor = await db.execute(
        """
        SELECT id, streak, max_streak
        FROM streaks
        WHERE chat_id=? AND executor=?
        """,
        (chat_id, executor)
    )

    row = await cursor.fetchone()

    if not row:

        streak = 1 if success else 0

        await db.execute(
            """
            INSERT INTO streaks
            (chat_id, executor, streak, max_streak)
            VALUES (?, ?, ?, ?)
            """,
            (chat_id, executor, streak, streak)
        )

    else:

        row_id, current, maximum = row

        if success:
            current += 1
            maximum = max(maximum, current)
        else:
            current = 0

        await db.execute(
            """
            UPDATE streaks
            SET streak=?, max_streak=?
            WHERE id=?
            """,
            (current, maximum, row_id)
        )

    await db.commit()
```

async def get_streak(chat_id, executor):
async with aiosqlite.connect(DB_NAME) as db:
cursor = await db.execute(
"""
SELECT streak, max_streak
FROM streaks
WHERE chat_id=? AND executor=?
""",
(chat_id, executor)
)
return await cursor.fetchone()

# =====================================

# STATS

# =====================================

async def get_rating(chat_id):
async with aiosqlite.connect(DB_NAME) as db:
cursor = await db.execute(
"""
SELECT executor, COUNT(*)
FROM tasks
WHERE chat_id=?
AND status='done'
GROUP BY executor
ORDER BY COUNT(*) DESC
""",
(chat_id,)
)
return await cursor.fetchall()

async def get_stats(chat_id):
async with aiosqlite.connect(DB_NAME) as db:
cursor = await db.execute(
"""
SELECT executor,
SUM(CASE WHEN status='done' THEN 1 ELSE 0 END),
SUM(CASE WHEN status='active' THEN 1 ELSE 0 END)
FROM tasks
WHERE chat_id=?
GROUP BY executor
""",
(chat_id,)
)
return await cursor.fetchall()
