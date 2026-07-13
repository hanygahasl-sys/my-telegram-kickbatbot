"""
orchestrator.py — точка входа Multi-Agent системы.

Цепочка:
    Telegram (raw_text)
        → analyst.analyse()   → dict
        → writer.write()      → str (черновик)
        → editor.edit()       → str (финальный пост)
        → Telegram «Избранное»
"""

import os
import logging
import asyncio
from telethon import TelegramClient, events
from dotenv import load_dotenv

from analyst import analyse
from writer import write
from editor import edit

load_dotenv()

# ──────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# TELEGRAM CONFIG
# ──────────────────────────────────────────────
CHANNELS = [-1003895656743, -1003838037947]

MIN_MESSAGE_LENGTH = 50   # сообщения короче игнорируются
POST_DELAY_SEC     = 5    # пауза после отправки (против флуда)

client = TelegramClient(
    "my_session",
    os.getenv("API_ID"),
    os.getenv("API_HASH"),
)
# ──────────────────────────────────────────────


async def run_pipeline(raw_text: str, source_chat_id: int) -> str:
    """
    Запускает цепочку агентов и возвращает финальный пост.

    Каждый агент — корутина; await гарантирует, что следующий шаг
    стартует только после завершения предыдущего.
    """
    logger.info("[Pipeline] Старт для канала %s", source_chat_id)

    # Шаг 1: Analyst — сырой текст → структурированные факты
    analysis: dict = await analyse(raw_text)

    # Шаг 2: Writer — факты → эмоциональный черновик
    draft: str = await write(analysis)

    # Шаг 3: Editor — черновик → сбалансированный финальный пост
    final_post: str = await edit(draft)

    logger.info("[Pipeline] Готово.")
    return final_post


@client.on(events.NewMessage(chats=CHANNELS))
async def handler(event):
    # ... (твой код)
    
    # ДОБАВЬ ЭТО СРАЗУ ПОСЛЕ ПРИЕМА СООБЩЕНИЯ
    # Это заставит бота обрабатывать не более 1 поста в минуту
    await asyncio.sleep(60) 
    
    try:
        final_post = await run_pipeline(event.raw_text, event.chat_id)
        # ...

        header = f"✍️ НОВЫЙ ПОСТ (источник: {event.chat_id})\n{'─' * 32}\n\n"
        await client.send_message("me", header + final_post)

        await asyncio.sleep(POST_DELAY_SEC)

    except ValueError as exc:
        # Analyst не смог распарсить JSON
        msg = f"⚠️ Ошибка Analyst (невалидный JSON):\n{exc}"
        logger.error(msg)
        await client.send_message("me", msg)

    except RuntimeError as exc:
        # Все retry на 429 исчерпаны
        msg = f"⚠️ Gemini API недоступен:\n{exc}"
        logger.error(msg)
        await client.send_message("me", msg)

    except Exception as exc:
        msg = f"⚠️ Непредвиденная ошибка:\n{exc}"
        logger.exception(msg)
        await client.send_message("me", msg)


# ──────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Бот запущен. Слушаю каналы: %s", CHANNELS)
    client.start()
    client.run_until_disconnected()