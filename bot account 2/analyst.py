"""
analyst.py — Агент-аналитик.

Вход:  str  (сырой текст из Telegram)
Выход: dict (структурированные факты в формате JSON)
"""

import json
import logging
from gemini_utils import gemini_generate

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# AGENT IDENTITY  (edit freely)
# ──────────────────────────────────────────────
SYSTEM_INSTRUCTION = (
    "Ты — объективный исследователь. "
    "Твоя задача: найти в сыром тексте суть, отбросить шелуху, "
    "выделить главную проблему или неочевидный факт. "
    "Будь сухим и рациональным."
)

PROMPT_TEMPLATE = """
Проанализируй текст ниже и верни ТОЛЬКО валидный JSON — без пояснений, без markdown-блоков.

Структура JSON:
{{
  "main_topic": "одна фраза — о чём текст",
  "key_facts": ["факт 1", "факт 2", "факт 3"],
  "hidden_insight": "неочевидный вывод, который большинство пропустит",
  "core_problem": "главное противоречие или проблема, если есть"
}}

Исходный текст:
{raw_text}
"""
# ──────────────────────────────────────────────


async def analyse(raw_text: str) -> dict:
    """
    Принимает сырой текст, возвращает словарь с фактами.
    Выбрасывает ValueError, если модель не вернула валидный JSON.
    """
    logger.info("[Analyst] Анализирую текст...")

    raw_json = await gemini_generate(
        prompt=PROMPT_TEMPLATE.format(raw_text=raw_text),
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.2,
        top_p=0.9,
    )

    # На случай если модель всё же обернула ответ в ```json ... ```
    if raw_json.startswith("```"):
        raw_json = raw_json.split("```")[1]
        if raw_json.startswith("json"):
            raw_json = raw_json[4:]

    try:
        result = json.loads(raw_json)
        logger.info("[Analyst] Готово: %s", result.get("main_topic", "—"))
        return result
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"[Analyst] Невалидный JSON от модели:\n{raw_json}"
        ) from exc