import aiosqlite
from datetime import datetime, timedelta
import pytz

KIEV_TZ = pytz.timezone("Europe/Kyiv")
DB_NAME = "quests.db"


def _now_kiev():
    return datetime.now(KIEV_TZ).replace(tzinfo=None)


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
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
                reminded_steps TEXT DEFAULT '',
                last_message_id INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                streak INTEGER DEFAULT 0,
                last_check_date TEXT DEFAULT '',
                last_reminded_time TEXT,
                last_message_id INTEGER
            )
        """)
        await db.commit()


# --- Квесты ---

async def add_quest(user_id, title, deadline, category):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO quests (user_id, title, deadline, created_at, category, reminded_steps) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, title, deadline, _now_kiev().isoformat(), category, ""),
        )
        await db.commit()


async def get_quests(user_id, category=None):
    async with aiosqlite.connect(DB_NAME) as db:
        if category:
            query = (
                "SELECT id, title, deadline, created_at FROM quests "
                "WHERE user_id = ? AND status = 'active' AND category = ?"
            )
            params = (user_id, category)
        else:
            query = (
                "SELECT id, title, deadline, created_at FROM quests "
                "WHERE user_id = ? AND status = 'active'"
            )
            params = (user_id,)
        async with db.execute(query, params) as cursor:
            return await cursor.fetchall()


async def change_quest_status(quest_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE quests SET status = ?, finished_at = ? WHERE id = ?",
            (status, _now_kiev().isoformat(), quest_id),
        )
        await db.commit()


async def get_quest_last_message_id(quest_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT last_message_id FROM quests WHERE id = ?", (quest_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def clear_quest_last_message_id(quest_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE quests SET last_message_id = NULL WHERE id = ?", (quest_id,)
        )
        await db.commit()


async def get_active_quests_for_deadlines():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT id, user_id, title, deadline, reminded_steps FROM quests WHERE status = 'active'"
        ) as cursor:
            return await cursor.fetchall()


async def mark_quest_failed(quest_id, finished_at):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE quests SET status = 'failed', finished_at = ? WHERE id = ?",
            (finished_at, quest_id),
        )
        await db.commit()


async def update_quest_reminded_steps(quest_id, step_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE quests SET reminded_steps = ? WHERE id = ?", (step_id, quest_id)
        )
        await db.commit()


async def get_active_quests_grouped_by_user():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT user_id, title FROM quests WHERE status = 'active'"
        ) as cursor:
            rows = await cursor.fetchall()
    users_tasks = {}
    for user_id, title in rows:
        users_tasks.setdefault(user_id, []).append(title)
    return users_tasks


async def get_categories(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT DISTINCT category FROM quests WHERE user_id = ? AND category IS NOT NULL",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


# --- Привычки ---

async def add_habit(user_id, title):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO habits (user_id, title, last_check_date) VALUES (?, ?, ?)",
            (user_id, title, ""),
        )
        await db.commit()


async def get_habits(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT id, title, streak FROM habits WHERE user_id = ?", (user_id,)
        ) as cursor:
            return await cursor.fetchall()


async def check_habit(habit_id):
    now_kiev = _now_kiev()
    today = now_kiev.strftime("%Y-%m-%d")
    yesterday = (now_kiev - timedelta(days=1)).strftime("%Y-%m-%d")

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT streak, last_check_date FROM habits WHERE id = ?", (habit_id,)
        ) as cursor:
            result = await cursor.fetchone()

        if not result:
            return False, 0

        streak, last_date = result
        if last_date == today:
            return False, streak

        new_streak = streak + 1 if last_date == yesterday else 1

        await db.execute(
            """
            UPDATE habits
            SET streak = ?, last_check_date = ?, last_reminded_time = NULL, last_message_id = NULL
            WHERE id = ?
            """,
            (new_streak, today, habit_id),
        )
        await db.commit()
        return True, new_streak


async def get_habit_last_message_id(habit_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT last_message_id FROM habits WHERE id = ?", (habit_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def clear_habit_last_message_id(habit_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE habits SET last_message_id = NULL WHERE id = ?", (habit_id,)
        )
        await db.commit()


async def get_habits_for_reminder(today, reminder_type):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT user_id, title, id, last_message_id FROM habits "
            "WHERE last_check_date != ? AND (last_reminded_time IS NULL OR last_reminded_time != ?)",
            (today, reminder_type),
        ) as cursor:
            return await cursor.fetchall()


async def update_habit_reminder(habit_id, reminder_type, message_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE habits SET last_reminded_time = ?, last_message_id = ? WHERE id = ?",
            (reminder_type, message_id, habit_id),
        )
        await db.commit()


# --- Статистика ---

async def get_stats(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT status, COUNT(*) FROM quests WHERE user_id = ? GROUP BY status",
            (user_id,),
        ) as cursor:
            return await cursor.fetchall()


async def get_daily_stats(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        today = _now_kiev().strftime("%Y-%m-%d")
        async with db.execute(
            "SELECT COUNT(*) FROM quests WHERE user_id = ? AND status = 'won' AND date(finished_at) = ?",
            (user_id, today),
        ) as cursor:
            done = (await cursor.fetchone())[0]
        async with db.execute(
            "SELECT COUNT(*) FROM quests WHERE user_id = ? AND status = 'failed' AND date(finished_at) = ?",
            (user_id, today),
        ) as cursor:
            fail = (await cursor.fetchone())[0]
        return done, fail
async def update_quest_last_message_id(quest_id, message_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE quests SET last_message_id = ? WHERE id = ?", 
            (message_id, quest_id)
        )
        await db.commit()


# --- Архив квестов (Победы / Поражения с пагинацией) ---
# Отдельная таблица не заводится: колонки title/status/finished_at
# уже есть в quests и заполняются в change_quest_status/mark_quest_failed.

async def get_quest_history_count(user_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM quests WHERE user_id = ? AND status = ?",
            (user_id, status),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_quest_history_page(user_id, status, offset, limit):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT title, finished_at FROM quests "
            "WHERE user_id = ? AND status = ? "
            "ORDER BY finished_at DESC LIMIT ? OFFSET ?",
            (user_id, status, limit, offset),
        ) as cursor:
            return await cursor.fetchall()