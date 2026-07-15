import re
import pytz
from datetime import datetime, timedelta

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import database

KIEV_TZ = pytz.timezone("Europe/Kiev")


def get_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Мои квесты", callback_data="go_list")],
        [InlineKeyboardButton(text="🔥 Мои привычки", callback_data="go_habits")],
        [InlineKeyboardButton(text="➕ Добавить квест", callback_data="go_add")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="go_stats")],
        [InlineKeyboardButton(text="📂 Категории", callback_data="go_categories")],
        [InlineKeyboardButton(text="🧠 Мотивация", callback_data="get_motivation")],
    ])


async def cleanup_quest_message(bot, user_id, quest_id):
    message_id = await database.get_quest_last_message_id(quest_id)
    if message_id:
        try:
            await bot.delete_message(chat_id=user_id, message_id=message_id)
        except Exception:
            pass
        await database.clear_quest_last_message_id(quest_id)


async def cleanup_habit_message(bot, user_id, habit_id):
    message_id = await database.get_habit_last_message_id(habit_id)
    if message_id:
        try:
            await bot.delete_message(chat_id=user_id, message_id=message_id)
        except Exception:
            pass
        await database.clear_habit_last_message_id(habit_id)


async def get_habits_markup(user_id):
    habits = await database.get_habits(user_id)
    kb = [[InlineKeyboardButton(text=f"{h[1]} | 🔥 {h[2]}", callback_data=f"habit_{h[0]}")] for h in habits]
    kb.append([InlineKeyboardButton(text="➕ Добавить привычку", callback_data="start_add_habit")])
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="go_start")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def parse_deadline(text):
    hours_match = re.search(r'(\d+)ч', text)
    minutes_match = re.search(r'(\d+)м', text)
    hours = int(hours_match.group(1)) if hours_match else 0
    minutes = int(minutes_match.group(1)) if minutes_match else 0
    now = datetime.now(KIEV_TZ).replace(tzinfo=None)
    if not hours_match and not minutes_match:
        return now + timedelta(hours=24)
    return now + timedelta(hours=hours, minutes=minutes)
