import asyncio
import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import database
from handlers import router
from datetime import datetime, timedelta
import aiosqlite
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Функция для фоновой проверки дедлайнов
async def check_deadlines(bot: Bot):
    while True:
        await asyncio.sleep(60)
        try:
            async with aiosqlite.connect("quests.db") as db:
                async with db.execute("SELECT id, user_id, title, deadline, reminded_steps FROM quests WHERE status = 'active'") as cursor:
                    rows = await cursor.fetchall()
                    
                    now = datetime.now()
                    for row in rows:
                        q_id, user_id, title, deadline_str, reminded_steps = row
                        deadline = datetime.fromisoformat(deadline_str)
                        seconds_left = int((deadline - now).total_seconds())
                        
                        if seconds_left <= 0:
                            await db.execute(
                                "UPDATE quests SET status = 'failed', finished_at = ? WHERE id = ?", 
                                (now.isoformat(), q_id)
                            )
                            await db.commit()
                            await bot.send_message(user_id, f"💀 Квест «{title}» провален!\n\nТы проиграл свою гонку, сынок.")
                            continue 

                        thresholds = [
                            (43200, "12ч", "12"),
                            (21600, "6ч", "6"),
                            (3600, "1ч", "1"),
                            (1800, "30м", "0.5")
                        ]
                        
                        current_steps = str(reminded_steps) if reminded_steps else ""
                        for sec, text, step_id in thresholds:
                            if seconds_left <= sec and step_id not in current_steps.split(','):
                                if seconds_left > (sec - 300):
                                    await bot.send_message(
                                        user_id, 
                                        f"⚠️ **Напоминание!**\n\nКвест «{title}» заканчивается через {text}!",
                                        parse_mode="Markdown"
                                    )
                                new_steps = (current_steps + "," if current_steps else "") + step_id
                                await db.execute("UPDATE quests SET reminded_steps = ? WHERE id = ?", (new_steps, q_id))
                                await db.commit()
                                break 
        except Exception as e:
            print(f"Ошибка в фоновой задаче квестов: {e}")

# Функция напоминания о привычках
async def check_habit_reminders(bot: Bot):
    while True:
        # Проверяем раз в час
        await asyncio.sleep(3600)
        try:
            async with aiosqlite.connect("quests.db") as db:
                today = datetime.now().strftime("%Y-%m-%d")
                async with db.execute("SELECT user_id, title, last_check_date FROM habits") as cursor:
                    habits = await cursor.fetchall()
                    for user_id, title, last_date in habits:
                        if last_date != today:
                            await bot.send_message(
                                user_id, 
                                f"🔥 **Привычка ждет!**\n\nТы еще не отметился в привычке «{title}» на сегодня. Не позволяй серии прерваться!"
                            )
        except Exception as e:
            print(f"Ошибка в напоминании о привычках: {e}")

# Функция для утреннего отчета
async def morning_digest(bot: Bot):
    while True:
        now = datetime.now()
        target = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        
        await asyncio.sleep((target - now).total_seconds())
        try:
            async with aiosqlite.connect("quests.db") as db:
                async with db.execute("SELECT user_id, title FROM quests WHERE status = 'active'") as cursor:
                    rows = await cursor.fetchall()
                    users_tasks = {}
                    for user_id, title in rows:
                        if user_id not in users_tasks: users_tasks[user_id] = []
                        users_tasks[user_id].append(title)
                    for user_id, titles in users_tasks.items():
                        tasks_list = "\n".join([f"• {t}" for t in titles])
                        await bot.send_message(user_id, f"☀️ **Доброе утро!**\n\nТвои задачи на сегодня:\n{tasks_list}\n\nНе облажайся, сынок.")
        except Exception as e:
            print(f"Ошибка в утреннем дайджесте: {e}")
        await asyncio.sleep(60)

async def main():
    load_dotenv()
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()
    await database.init_db()
    dp.include_router(router)
    
    # Запускаем все задачи
    asyncio.create_task(check_deadlines(bot))
    asyncio.create_task(morning_digest(bot))
    asyncio.create_task(check_habit_reminders(bot)) 
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())