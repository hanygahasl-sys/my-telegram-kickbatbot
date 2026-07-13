"""
writer.py — Агент-писатель.

Вход:  dict (выход Analyst)
Выход: str  (черновик Telegram-поста)
"""

import logging
from gemini_utils import gemini_generate

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# AGENT IDENTITY  (edit freely)
# ──────────────────────────────────────────────
SYSTEM_INSTRUCTION = (
    "Ты — творческий сценарист. "
    "Твоя задача: упаковать выводы аналитика в захватывающую форму. "
    "Используй метафоры, сторителлинг, ломай стереотипы. "
    "Твоя цель — вызвать эмоциональный отклик у читателя."
)

PROMPT_TEMPLATE = """
На основе аналитических данных напиши черновик поста для Telegram-канала.

Аналитика:
- Тема: {main_topic}
- Ключевые факты: {key_facts}
- Скрытый инсайт: {hidden_insight}
- Главная проблема: {core_problem}

СТРУКТУРА ПОСТА:
1. Заголовок — провокационный, цепляющий, без кликбейта-пустышки.
2. Хук — первое предложение бьёт в боль или ломает стереотип.
3. Основная часть — раскрой через парадоксальный угол. Метафоры приветствуются.
   Абзацы — не длиннее 4 строк.
4. Финал — открытый вопрос, который провоцирует комментарий.

Пиши только текст поста, без пояснений и технических меток.
"""
# ──────────────────────────────────────────────


async def write(analysis: dict) -> str:
    """
    Принимает словарь от Analyst, возвращает черновик поста (str).
    """
    logger.info("[Writer] Пишу черновик...")

    draft = await gemini_generate(
        prompt=PROMPT_TEMPLATE.format(
            main_topic=analysis.get("main_topic", ""),
            key_facts=", ".join(analysis.get("key_facts", [])),
            hidden_insight=analysis.get("hidden_insight", ""),
            core_problem=analysis.get("core_problem", ""),
        ),
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.85,
        top_p=0.95,
    )

    logger.info("[Writer] Черновик готов.")
    return draft