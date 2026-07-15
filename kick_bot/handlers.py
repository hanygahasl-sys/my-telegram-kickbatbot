import random
import re
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import database
from phrases import WIN_PHRASES, FAIL_PHRASES, MOTIVATION_PHRASES
from utils import (
    KIEV_TZ,
    get_main_kb,
    cleanup_quest_message,
    cleanup_habit_message,
    get_habits_markup,
    parse_deadline,
)

router = Router()


class QuestStates(StatesGroup):
    menu = State()
    view_list = State()
    add_quest = State()
    add_habit = State()
    stats = State()


@router.message(Command("start"))
async def cmd_start(msg: Message, state: FSMContext):
    await state.set_state(QuestStates.menu)
    await msg.answer(
        "🎮 **Quest Manager**\nВыберите действие:",
        reply_markup=get_main_kb(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "go_start")
async def back_to_menu(call: CallbackQuery, state: FSMContext):
    await state.set_state(QuestStates.menu)
    await call.message.edit_text(
        "🎮 **Quest Manager**\nВыберите действие:",
        reply_markup=get_main_kb(),
        parse_mode="Markdown",
    )
    await call.answer()


@router.callback_query(F.data == "go_list")
async def show_list(call: CallbackQuery, state: FSMContext):
    await state.set_state(QuestStates.view_list)
    quests = await database.get_quests(call.from_user.id)
    text = "📋 **Ваши задачи:**\n\n"
    kb_list = []
    if not quests:
        text += "Пусто."
    else:
        for q in quests:
            deadline = datetime.fromisoformat(q[2]) if isinstance(q[2], str) else q[2]
            created = datetime.fromisoformat(q[3]) if isinstance(q[3], str) else q[3]
            remaining = deadline - datetime.now(KIEV_TZ).replace(tzinfo=None)
            total_seconds = int(remaining.total_seconds())
            timer = (
                f"⏳ {total_seconds // 3600}ч {(total_seconds % 3600) // 60}м"
                if total_seconds > 0
                else "⏰ Истекло!"
            )
            text += f"⚔️ {q[1]}\n📅 Назначено: {created.strftime('%d.%m %H:%M')} | {timer}\n\n"
            kb_list.append([
                InlineKeyboardButton(text="✅ Победа", callback_data=f"win_{q[0]}"),
                InlineKeyboardButton(text="❌ Сдаться", callback_data=f"fail_{q[0]}"),
            ])
    kb_list.append([InlineKeyboardButton(text="🔙 Назад", callback_data="go_start")])
    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_list),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith(("win_", "fail_")))
async def process_quest_result(call: CallbackQuery, state: FSMContext):
    action, quest_id = call.data.split("_")
    await cleanup_quest_message(call.bot, call.from_user.id, int(quest_id))
    status = "won" if action == "win" else "failed"
    phrase = random.choice(WIN_PHRASES if action == "win" else FAIL_PHRASES)
    await database.change_quest_status(quest_id, status)
    await call.answer(text=phrase, show_alert=True)
    await show_list(call, state)


@router.callback_query(F.data == "go_add")
async def start_add(call: CallbackQuery, state: FSMContext):
    await state.set_state(QuestStates.add_quest)
    msg = await call.message.edit_text(
        "✍️ Введите название задачи (например: Бег 5ч #спорт):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="go_start")],
        ]),
    )
    await state.update_data(last_msg_id=msg.message_id)


@router.message(QuestStates.add_quest)
async def process_add(msg: Message, state: FSMContext):
    deadline = parse_deadline(msg.text)
    clean_title = re.sub(r'\s*\d+ч', '', msg.text)
    category = clean_title.split("#")[-1].strip().lower() if "#" in clean_title else "общие"
    await database.add_quest(msg.from_user.id, clean_title, deadline.isoformat(), category)
    data = await state.get_data()
    await msg.delete()
    await state.set_state(QuestStates.menu)
    await msg.bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=data.get("last_msg_id"),
        text="✅ Квест добавлен!\n\n🎮 **Quest Manager**\nВыберите действие:",
        reply_markup=get_main_kb(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "go_habits")
async def show_habits(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "🔥 **Твои привычки:**",
        reply_markup=await get_habits_markup(call.from_user.id),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "start_add_habit")
async def start_add_habit(call: CallbackQuery, state: FSMContext):
    await state.set_state(QuestStates.add_habit)
    msg = await call.message.edit_text(
        "✍️ Введите название новой привычки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="go_habits")],
        ]),
    )
    await state.update_data(last_msg_id=msg.message_id)


@router.message(QuestStates.add_habit)
async def process_add_habit(msg: Message, state: FSMContext):
    await database.add_habit(msg.from_user.id, msg.text)
    await msg.delete()
    data = await state.get_data()
    await msg.bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=data.get("last_msg_id"),
        text="✅ Привычка добавлена!\n\n🔥 **Твои привычки:**",
        reply_markup=await get_habits_markup(msg.from_user.id),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("habit_"))
async def process_habit(call: CallbackQuery, state: FSMContext):
    h_id = int(call.data.split("_")[1])
    await cleanup_habit_message(call.bot, call.from_user.id, h_id)
    success, streak = await database.check_habit(h_id)
    await call.answer(
        f"✅ Отлично! Твоя серия: {streak} дней!" if success else f"Уже отмечал. Серия: {streak} дней.",
        show_alert=True,
    )
    await show_habits(call, state)


@router.callback_query(F.data == "go_stats")
async def show_stats(call: CallbackQuery, state: FSMContext):
    stats_data = await database.get_stats(call.from_user.id)
    stats_dict = {row[0]: row[1] for row in stats_data}
    won, failed = stats_dict.get('won', 0), stats_dict.get('failed', 0)
    daily_won, daily_failed = await database.get_daily_stats(call.from_user.id)
    text = (
        f"📊 **Статистика:**\n\nОбщая:\n✅ Побед: {won} | ❌ Поражений: {failed}\n\n"
        f"За сегодня:\n✅ Выполнено: {daily_won} | 💀 Провалено: {daily_failed}"
    )
    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="go_start")],
        ]),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "go_categories")
async def show_categories(call: CallbackQuery, state: FSMContext):
    cats = await database.get_categories(call.from_user.id)
    kb = [[InlineKeyboardButton(text=f"#{c}", callback_data=f"cat_{c}")] for c in cats]
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="go_start")])
    await call.message.edit_text("📂 Ваши категории:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))


@router.callback_query(F.data.startswith("cat_"))
async def show_category_quests(call: CallbackQuery, state: FSMContext):
    category = call.data.split("_")[1]
    quests = await database.get_quests(call.from_user.id, category=category)
    text = f"📂 Квесты в категории #{category}:\n\n"
    kb_list = [
        [
            InlineKeyboardButton(text="✅ Победа", callback_data=f"win_{q[0]}"),
            InlineKeyboardButton(text="❌ Сдаться", callback_data=f"fail_{q[0]}"),
        ]
        for q in quests
    ]
    kb_list.append([InlineKeyboardButton(text="🔙 Назад", callback_data="go_categories")])
    await call.message.edit_text(
        text if quests else "Пусто.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_list),
    )


@router.callback_query(F.data == "get_motivation")
async def send_motivation(call: CallbackQuery):
    await call.answer(text=random.choice(MOTIVATION_PHRASES), show_alert=True)
