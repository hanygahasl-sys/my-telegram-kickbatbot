import os
import asyncio
from telethon import TelegramClient, events
from dotenv import load_dotenv
from google import genai # Убедитесь, что установлен google-genai

load_dotenv()

# Используем переменные среды (создайте файл .env с этими данными)
client_ai = genai.Client(api_key=os.getenv('GEMINI_KEY'))
client = TelegramClient('my_session', os.getenv('API_ID'), os.getenv('API_HASH'))

@client.on(events.NewMessage(chats=-1003895656743))
async def handler(event):
    # Явно получаем текст сообщения
    message = event.raw_text 
    
    if message:
        print(f"Анализирую: {message[:30]}...")
        try:
            prompt = f"""
        Ты — жесткий редактор Telegram-каналов. 
        Твоя задача: взять текст и превратить его в один готовый пост.
        - Никаких предисловий («Вот варианты...», «Как редактор...»).
        - Никаких перечислений «Вариант 1», «Вариант 2».
        - Сразу пиши финальный текст поста.
        - Используй короткие абзацы, умеренное количество эмодзи.
        - Стиль: дерзкий, ироничный, короткий.
        
        Текст для переработки: {message}
        """
            # Используем модель, которая есть в твоем списке
            response = client_ai.models.generate_content(
                model='models/gemini-2.5-flash-lite', 
                contents=prompt
            )
            await client.send_message('me', f"Нейро-пост:\n{response.text}")
            await asyncio.sleep(30)
            print("Готово!")
        except Exception as e:
            print(f"Ошибка при работе с ИИ: {e}")

client.start()
client.run_until_disconnected()