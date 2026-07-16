import asyncio
import logging
from datetime import datetime, timedelta

import pytz
from aiogram import Bot

import database

logger = logging.getLogger(__name__)

KIEV_TZ = pytz.timezone("Europe/Kyiv")

# Пороги ОБЯЗАТЕЛЬНО должны идти от МЕНЬШЕГО к БОЛЬШЕМУ,
# иначе цикл в check_deadlines всегда будет находить "48ч" первым.
DEADLINE_THRESHOLDS = [
    (1800, "30м", "0.5"),
    (3600, "1ч", "1"),
    (21600, "6ч", "6"),
    (43200, "12ч", "12"),
    (172800, "48ч", "48"),
]


async def check_deadlines(bot: Bot):
    logger.info("Задача check_deadlines запущена.")
    while True:
        try:
            now = datetime.now(KIEV_TZ).replace(tzinfo=None)
            rows = await database.get_active_quests_for_deadlines()
        except Exception as e:
            logger.error(f"Ошибка получения квестов в check_deadlines: {e}")
            await asyncio.sleep(60)
            continue

        for q_id, user_id, title, deadline_str, reminded_steps in rows:
            try:
                deadline = datetime.fromisoformat(deadline_str)
                seconds_left = int((deadline - now).total_seconds())

                if seconds_left <= 0:
                    old_msg_id = await database.get_quest_last_message_id(q_id)
                    if old_msg_id:
                        try:
                            await bot.delete_message(chat_id=user_id, message_id=old_msg_id)
                        except Exception as e:
                            logger.debug(f"Не удалось удалить сообщение {old_msg_id} квеста {q_id}: {e}")
                    await database.mark_quest_failed(q_id, now.isoformat())
                    await bot.send_message(user_id, f"💀 Квест «{title}» провален!")
                    continue

                for sec, text, step_id in DEADLINE_THRESHOLDS:
                    if seconds_left <= sec:
                        if reminded_steps != step_id:
                            # 1. Удаляем старое сообщение, если оно есть
                            old_msg_id = await database.get_quest_last_message_id(q_id)
                            if old_msg_id:
                                try:
                                    await bot.delete_message(chat_id=user_id, message_id=old_msg_id)
                                except Exception as e:
                                    logger.debug(f"Не удалось удалить сообщение {old_msg_id} квеста {q_id}: {e}")

                            # 2. Отправляем новое сообщение
                            msg = await bot.send_message(
                                user_id,
                                f"⚠️ **Напоминание!**\n\nКвест «{title}» заканчивается через {text}!",
                                parse_mode="Markdown",
                            )

                            # 3. Сохраняем ID нового сообщения и обновляем шаг
                            await database.update_quest_reminded_steps(q_id, step_id)
                            await database.update_quest_last_message_id(q_id, msg.message_id)
                        break
            except Exception as e:
                logger.error(f"Ошибка обработки квеста {q_id}: {e}")
                continue

        await asyncio.sleep(60)


async def check_habit_reminders(bot: Bot):
    logger.info("Задача check_habit_reminders запущена.")
    while True:
        await asyncio.sleep(300)
        try:
            now = datetime.now(KIEV_TZ)
            hour = now.hour
            reminder_type = (
                "morning" if 9 <= hour < 10 else ("evening" if 20 <= hour < 21 else None)
            )
            if not reminder_type:
                continue

            today = now.strftime("%Y-%m-%d")
            habits = await database.get_habits_for_reminder(today, reminder_type)

            for user_id, title, h_id, last_message_id in habits:
                if last_message_id:
                    try:
                        await bot.delete_message(chat_id=user_id, message_id=last_message_id)
                    except Exception as e:
                        logger.debug(f"Не удалось удалить сообщение {last_message_id} привычки {h_id}: {e}")

                msg = await bot.send_message(
                    user_id,
                    f"🔥 **Привычка ждет!**\n\nТы еще не отметился в привычке «{title}» на сегодня.",
                )
                await database.update_habit_reminder(h_id, reminder_type, msg.message_id)
        except Exception as e:
            logger.error(f"Ошибка в check_habit_reminders: {e}")


async def morning_digest(bot: Bot):
    logger.info("Задача morning_digest запущена.")
    while True:
        now = datetime.now(KIEV_TZ)
        target = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())

        try:
            users_tasks = await database.get_active_quests_grouped_by_user()
            for user_id, titles in users_tasks.items():
                tasks_list = "\n".join(f"• {t}" for t in titles)
                await bot.send_message(
                    user_id,
                    f"☀️ **Доброе утро!**\n\nТвои задачи на сегодня:\n{tasks_list}",
                )
        except Exception as e:
            logger.error(f"Ошибка в утреннем дайджесте: {e}")

        await asyncio.sleep(60)
