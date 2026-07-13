import aiosqlite
from datetime import datetime

DB_NAME = "quests.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Добавили reminded_steps TEXT DEFAULT ''
        await db.execute("""
            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                deadline TIMESTAMP,
                created_at TIMESTAMP,
                finished_at TIMESTAMP,
                category TEXT,
                status TEXT DEFAULT 'active',
                reminded_steps TEXT DEFAULT ''
            )
        """)
        await db.commit()

async def add_quest(user_id, title, deadline, category):
    async with aiosqlite.connect(DB_NAME) as db:
        # Добавили reminded_steps в INSERT
        await db.execute(
            "INSERT INTO quests (user_id, title, deadline, created_at, category, reminded_steps) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, title, deadline, datetime.now().isoformat(), category, '')
        )
        await db.commit()

# --- Остальные функции оставляем без изменений ---

async def get_quests(user_id, category=None):
    async with aiosqlite.connect(DB_NAME) as db:
        query = "SELECT id, title, deadline, created_at FROM quests WHERE user_id = ? AND status = 'active'"
        params = [user_id]
        if category:
            query += " AND category = ?"
            params.append(category)
        async with db.execute(query, params) as cursor:
            return await cursor.fetchall()

async def get_categories(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT DISTINCT category FROM quests WHERE user_id = ? AND status = 'active'", (user_id,)) as cursor:
            return [row[0] for row in await cursor.fetchall()]

async def change_quest_status(quest_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE quests SET status = ?, finished_at = ? WHERE id = ?", (status, datetime.now().isoformat(), quest_id))
        await db.commit()

async def get_stats(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT status, COUNT(*) FROM quests WHERE user_id = ? GROUP BY status", (user_id,)) as cursor:
            return await cursor.fetchall()

async def get_quests_by_status(user_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT title, finished_at FROM quests WHERE user_id = ? AND status = ?", (user_id, status)) as cursor:
            return await cursor.fetchall()

async def get_daily_stats(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        today = datetime.now().strftime("%Y-%m-%d")
        async with db.execute(
            "SELECT COUNT(*) FROM quests WHERE user_id = ? AND status = 'won' AND date(finished_at) = ?",
            (user_id, today)
        ) as cursor:
            row_done = await cursor.fetchone()
            done_count = row_done[0] if row_done else 0
        
        async with db.execute(
            "SELECT COUNT(*) FROM quests WHERE user_id = ? AND status = 'failed' AND date(finished_at) = ?",
            (user_id, today)
        ) as cursor:
            row_failed = await cursor.fetchone()
            failed_count = row_failed[0] if row_failed else 0
        
        return done_count, failed_count