import aiosqlite
from datetime import datetime, timedelta

DB_NAME = "quests.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Создаем таблицу квестов
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
        # Создаем таблицу привычек
        await db.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                streak INTEGER DEFAULT 0,
                last_check_date TEXT DEFAULT ''
            )
        """)
        await db.commit()

# --- Функции для квестов ---

async def add_quest(user_id, title, deadline, category):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO quests (user_id, title, deadline, created_at, category, reminded_steps) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, title, deadline, datetime.now().isoformat(), category, '')
        )
        await db.commit()

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

async def get_daily_stats(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        today = datetime.now().strftime("%Y-%m-%d")
        async with db.execute("SELECT COUNT(*) FROM quests WHERE user_id = ? AND status = 'won' AND date(finished_at) = ?", (user_id, today)) as cursor:
            done_count = (await cursor.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM quests WHERE user_id = ? AND status = 'failed' AND date(finished_at) = ?", (user_id, today)) as cursor:
            failed_count = (await cursor.fetchone())[0]
        return done_count, failed_count

# --- Функции для привычек ---

async def add_habit(user_id, title):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO habits (user_id, title) VALUES (?, ?)", (user_id, title))
        await db.commit()

async def get_habits(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id, title, streak, last_check_date FROM habits WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchall()

async def check_habit(habit_id):
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT streak, last_check_date FROM habits WHERE id = ?", (habit_id,)) as cursor:
            result = await cursor.fetchone()
        
        if not result: return False, 0
        streak, last_date = result
            
        if last_date == today:
            return False, streak
            
        new_streak = streak + 1 if last_date == yesterday else 1
        await db.execute("UPDATE habits SET streak = ?, last_check_date = ? WHERE id = ?", (new_streak, today, habit_id))
        await db.commit()
        return True, new_streak