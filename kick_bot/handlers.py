import re
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import database
from datetime import datetime, timedelta
from phrases import WIN_PHRASES, FAIL_PHRASES
router = Router()

class QuestStates(StatesGroup):
    menu = State()
    view_list = State()
    add_quest = State()
    stats = State()

def get_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Мои квесты", callback_data="go_list")],
        [InlineKeyboardButton(text="➕ Добавить квест", callback_data="go_add")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="go_stats")],
        [InlineKeyboardButton(text="📂 Категории", callback_data="go_categories")],
        [InlineKeyboardButton(text="🧠 Мотивация", callback_data="get_motivation")]
    ])
import random # Не забудь импортировать в начале файла

# Список фраз
MOTIVATION_PHRASES = [
    # Твои личные фразы (суровый акцент)
    "Посредственность — твой удел?", "Держи диплом архитектора воздушных замков.",
    "И я забыл уже, о чем мечтал...", "Ты хочешь помочь всем, кроме себя, лол.",
    "Ответственность за свои мечты — только на твоих плечах.", "Возможно, это просто не прет?",
    "Проще убежать, спрятаться и забыть, не так ли?!", "Отдохнешь в гробу.",
    "Слабак.", "Ты такой же, как они...", 
    "Хватит имитировать бурную деятельность.", "Твоя лень — это твой главный враг.",
    "Ты сегодня сделал что-то для своей цели или просто просуществовал?",
    "Мир не изменится от твоих мыслей, только от действий.", "Больно будет только в начале.",

    # Цитаты и жесткие наставления
    "Дисциплина — это мост между целями и достижениями.", "Не ной, просто сделай это.",
    "Победа не любит слабаков. Продолжай.", "Твой успех начинается там, где заканчивается зона комфорта.",
    "Твои отговорки — это просто страх перед работой.", "Боль проходит, а результат остаётся навсегда.",
    "Не останавливайся, когда устал. Останавливайся, когда закончил.",
    "Успех — это сумма маленьких усилий, повторяемых изо дня в день.",
    "Тот, кто хочет — ищет возможности, кто не хочет — ищет причины.",
    "Если ты можешь об этом мечтать, ты можешь это сделать.",
    "Время — единственный ресурс, который нельзя восполнить. Не трать его впустую.",
    "Твой главный конкурент — это ты вчерашний.", "Действуй, пока другие планируют.",
    "Результат не приходит к тем, кто просто ждет.", "Сделай это сейчас, завтра превратится в никогда.",
    "Трудности — это просто ступени к успеху.", "Разница между тем, кто ты есть, и тем, кем ты хочешь стать — это твои действия.",
    "Лучший способ предсказать будущее — создать его.", "Удача — это то, что случается, когда подготовка встречается с возможностью.",
    "Не бойся ошибок, бойся бездействия.", "Твоя жизнь — это отражение твоих решений.",
    "Стань той версией себя, которой ты сам бы гордился.", "Дисциплина — это любовь к себе в будущем.",
    "Боль временна, гордость за результат — вечна.", "Сделай выбор: либо оправдания, либо результат.",
    "Упорство побеждает всё.", "Великие дела совершаются не силой, а упорством.",
    "Действие — это ключ к любому успеху.", "Будь дисциплинированным, когда никто не смотрит.",
    "Каждый пропущенный день — это шаг назад.", "Никто не придет и не сделает это за тебя.",
    "Ты сильнее, чем думаешь.", "Прекрати искать легкие пути.", "Риск — это часть пути.",
    "Твоя мечта не требует твоего сна.", "Будь лучше, чем вчера.", "Не сдавайся до последнего.",
    "Мастерство требует тысяч часов практики.", "Твои привычки определяют твое будущее.",
    "Верь в себя, даже когда другие сомневаются.", "Сфокусируйся на процессе, а не на результате.",
    "Не пытайся, делай.", "Просто начни.", "Движение — это жизнь.", "Результат — единственный критерий истины.",
    "Никаких оправданий. Только результат.", "Побеждай себя каждый день.", "Твой потенциал безграничен.",
    "Сделай это сегодня.", "Завтра — это ловушка.", "Твой путь уникален.", "Цени свое время.",
    "Дисциплина — это свобода.", "Борись до конца.", "Будь первым в своем деле.", "Верность своим целям.",
    "Сила воли — это мышца, тренируй её.", "Не жди идеального момента.", "Ошибки — это опыт.",
    "Твои амбиции должны быть больше твоих страхов.", "Смейся над трудностями.", "Будь неумолим к себе.",
    "Держи слово, данное самому себе.", "Успех — это не случайность.", "Цель оправдывает усилия.",
    "Преодолей себя.", "Дыши и двигайся вперед.", "Будь выше обстоятельств.", "Жизнь коротка для лени.",
    "Твой выбор сегодня — твой успех завтра.", "Развивайся или деградируй.", "Дисциплина — это характер.",
    "Твои действия громче слов.", "Никогда не оглядывайся назад.", "Стремись к совершенству.",
    "Каждый шаг важен.", "Упрямство в достижении цели — ключ к успеху.", "Твой успех — твоя ответственность."
]

@router.callback_query(F.data == "get_motivation")
async def send_motivation(call: CallbackQuery):
    phrase = random.choice(MOTIVATION_PHRASES)
    # show_alert=True сделает фразу всплывающим окном
    await call.answer(text=phrase, show_alert=True)

def parse_deadline(text):
    # Ищем часы
    hours_match = re.search(r'(\d+)ч', text)
    # Ищем минуты
    minutes_match = re.search(r'(\d+)м', text)
    
    hours = int(hours_match.group(1)) if hours_match else 0
    minutes = int(minutes_match.group(1)) if minutes_match else 0
    
    # Если вообще ничего не ввели, ставим 24 часа по умолчанию
    if not hours_match and not minutes_match:
        return datetime.now() + timedelta(hours=24)
        
    return datetime.now() + timedelta(hours=hours, minutes=minutes)

# --- ХЕНДЛЕРЫ ---

@router.message(Command("start"))
async def cmd_start(msg: Message, state: FSMContext):
    await state.set_state(QuestStates.menu)
    await msg.answer("🎮 **Quest Manager**\nВыберите действие:", reply_markup=get_main_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "go_start")
async def back_to_menu(call: CallbackQuery, state: FSMContext):
    await state.set_state(QuestStates.menu)
    await call.message.edit_text("🎮 **Quest Manager**\nВыберите действие:", reply_markup=get_main_kb(), parse_mode="Markdown")
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
            remaining = deadline - datetime.now()
            total_seconds = int(remaining.total_seconds())
            
            if total_seconds > 0:
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                timer = f"⏳ {hours}ч {minutes}м"
            else:
                timer = "⏰ Истекло!"
            
            text += f"⚔️ {q[1]}\n📅 Назначено: {created.strftime('%d.%m %H:%M')} | {timer}\n\n"
            kb_list.append([
                InlineKeyboardButton(text="✅ Победа", callback_data=f"win_{q[0]}"),
                InlineKeyboardButton(text="❌ Сдаться", callback_data=f"fail_{q[0]}")
            ])
            
    kb_list.append([InlineKeyboardButton(text="🔙 Назад", callback_data="go_start")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_list), parse_mode="Markdown")

@router.callback_query(F.data.startswith(("win_", "fail_")))
async def process_quest_result(call: CallbackQuery, state: FSMContext):
    action, quest_id = call.data.split("_")
    
    # Определяем статус и фразу
    if action == "win":
        status = "won"
        phrase = random.choice(WIN_PHRASES)
    else:
        status = "failed"
        phrase = random.choice(FAIL_PHRASES)
        
    await database.change_quest_status(quest_id, status)
    
    # Отправляем фразу всплывающим окном
    await call.answer(text=phrase, show_alert=True)
    
    # Обновляем список задач
    await show_list(call, state)

@router.callback_query(F.data == "go_add")
async def start_add(call: CallbackQuery, state: FSMContext):
    await state.set_state(QuestStates.add_quest)
    # Отправляем вопрос и сохраняем его ID в state
    msg = await call.message.edit_text(
        "✍️ Введите название задачи (например: Бег 5ч #спорт):", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="go_start")]])
    )
    await state.update_data(last_msg_id=msg.message_id)
    
@router.message(QuestStates.add_quest)
async def process_add(msg: Message, state: FSMContext):
    # 1. Логика добавления
    deadline = parse_deadline(msg.text)
    clean_title = re.sub(r'\s*\d+ч', '', msg.text)
    category = clean_title.split("#")[-1].strip().lower() if "#" in clean_title else "общие"
    await database.add_quest(msg.from_user.id, clean_title, deadline.isoformat(), category)
    
    # 2. Достаем ID сообщения, которое нужно превратить в меню
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    
    # 3. Удаляем сообщение с вводом
    await msg.delete()
    
    # 4. Редактируем старое сообщение бота (превращаем его в меню)
    await state.set_state(QuestStates.menu)
    await msg.bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=last_msg_id,
        text="✅ Квест добавлен!\n\n🎮 **Quest Manager**\nВыберите действие:",
        reply_markup=get_main_kb(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "go_stats")
async def show_stats(call: CallbackQuery, state: FSMContext):
    await state.set_state(QuestStates.stats)
    
    # Получаем общую статистику
    stats_data = await database.get_stats(call.from_user.id)
    stats_dict = {row[0]: row[1] for row in stats_data}
    won, failed = stats_dict.get('won', 0), stats_dict.get('failed', 0)
    
    # Получаем статистику за сегодня
    daily_won, daily_failed = await database.get_daily_stats(call.from_user.id)
    
    text = (
        f"📊 **Статистика:**\n\n"
        f"Общая:\n✅ Побед: {won} | ❌ Поражений: {failed}\n\n"
        f"За сегодня:\n✅ Выполнено: {daily_won} | 💀 Провалено: {daily_failed}\n"
        f"📈 Всего квестов: {won + failed}"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Выполненные", callback_data="view_won"),
         InlineKeyboardButton(text="❌ Проигранные", callback_data="view_failed")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="go_start")]
    ])
    
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.in_({"view_won", "view_failed"}))
async def view_history(call: CallbackQuery, state: FSMContext):
    status = "won" if call.data == "view_won" else "failed"
    quests = await database.get_quests_by_status(call.from_user.id, status)
    text = ("🏆 Выполненные:" if status == "won" else "💀 Проигранные:") + "\n\n"
    for q in quests:
        ftime = datetime.fromisoformat(q[1]).strftime('%d.%m %H:%M') if q[1] else "N/A"
        text += f"• {q[0]} ({ftime})\n"
    if not quests: text += "Пусто."
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="go_stats")]])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- ДОБАВЛЕННЫЕ ХЕНДЛЕРЫ ---

@router.callback_query(F.data == "go_categories")
async def show_categories(call: CallbackQuery, state: FSMContext):
    cats = await database.get_categories(call.from_user.id)
    kb = []
    for c in cats:
        kb.append([InlineKeyboardButton(text=f"#{c}", callback_data=f"cat_{c}")])
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="go_start")])
    await call.message.edit_text("📂 Ваши категории:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await call.answer()

@router.callback_query(F.data.startswith("cat_"))
async def show_category_quests(call: CallbackQuery, state: FSMContext):
    category = call.data.split("_")[1]
    quests = await database.get_quests(call.from_user.id, category=category)
    
    text = f"📂 Квесты в категории #{category}:\n\n"
    kb_list = []
    
    if not quests:
        text += "Пусто."
    else:
        for q in quests:
            # q[0]=id, q[1]=title, q[2]=deadline, q[3]=created_at
            deadline = datetime.fromisoformat(q[2]) if isinstance(q[2], str) else q[2]
            created = datetime.fromisoformat(q[3]) if isinstance(q[3], str) else q[3]
            
            # Расчет таймера
            remaining = deadline - datetime.now()
            total_seconds = int(remaining.total_seconds())
            
            if total_seconds > 0:
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                timer = f"⏳ {hours}ч {minutes}м"
            else:
                timer = "⏰ Истекло!"
            
            text += f"⚔️ {q[1]}\n📅 Назначено: {created.strftime('%d.%m %H:%M')} | {timer}\n\n"
            
            kb_list.append([
                InlineKeyboardButton(text="✅ Победа", callback_data=f"win_{q[0]}"),
                InlineKeyboardButton(text="❌ Сдаться", callback_data=f"fail_{q[0]}")
            ])
            
    kb_list.append([InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="go_categories")])
    
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_list), parse_mode="Markdown")
    await call.answer()