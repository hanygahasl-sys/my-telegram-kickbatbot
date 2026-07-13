"""
gemini_utils.py — общие утилиты для работы с Gemini API.

Содержит:
  - gemini_generate()  — единая async-обёртка с exponential backoff.
    Все агенты вызывают только её, не трогая SDK напрямую.
"""

import os
import asyncio
import logging
from google import genai
from google.genai import errors as genai_errors

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# RETRY CONFIG  (edit freely)
# ──────────────────────────────────────────────
RETRY_ATTEMPTS   = 5      # максимум попыток
BASE_DELAY_SEC   = 20     # начальная задержка при 429
MAX_DELAY_SEC    = 120    # потолок задержки
BACKOFF_FACTOR   = 2      # множитель для каждой следующей попытки
# ──────────────────────────────────────────────


async def gemini_generate(
    *,
    prompt: str,
    system_instruction: str,
    temperature: float,
    top_p: float = 0.9,
) -> str:
    """
    Асинхронно вызывает Gemini API с exponential backoff при ошибке 429.

    Параметры:
        prompt              — финальный текст запроса (уже отформатированный).
        system_instruction  — роль / личность агента.
        temperature         — температура генерации.
        top_p               — top-p сэмплирование.

    Возвращает:
        Текст ответа модели (str).

    Выбрасывает:
        RuntimeError — если все попытки исчерпаны.
        Exception    — любая не-429 ошибка пробрасывается немедленно.
    """
    ai_client = genai.Client(api_key=os.getenv("GEMINI_KEY"))
    delay = BASE_DELAY_SEC

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            # SDK-вызов синхронный — запускаем в пуле потоков,
            # чтобы не блокировать event loop Telethon.
            response = await asyncio.to_thread(
                ai_client.models.generate_content,
                model="models/gemini-2.5-flash-lite",
                contents=prompt,
                config={
                    "temperature": temperature,
                    "top_p": top_p,
                    "system_instruction": system_instruction,
                },
            )
            return response.text.strip()

        except genai_errors.ClientError as exc:
            # 429 Resource Exhausted
            if exc.code == 429:
                if attempt == RETRY_ATTEMPTS:
                    raise RuntimeError(
                        f"Gemini API вернул 429 {RETRY_ATTEMPTS} раз подряд. "
                        "Пайплайн прерван."
                    ) from exc

                logger.warning(
                    "[gemini_utils] 429 Resource Exhausted (попытка %d/%d). "
                    "Жду %d сек...",
                    attempt, RETRY_ATTEMPTS, delay,
                )
                await asyncio.sleep(delay)
                delay = min(delay * BACKOFF_FACTOR, MAX_DELAY_SEC)
            else:
                raise  # любая другая ошибка — пробрасываем сразу

    # сюда попасть нельзя, но для mypy
    raise RuntimeError("Неожиданный выход из retry-цикла.")