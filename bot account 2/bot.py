import os
import asyncio
from telethon import TelegramClient, events
from dotenv import load_dotenv
from google import genai 

load_dotenv()

client_ai = genai.Client(api_key=os.getenv('GEMINI_KEY'))
client = TelegramClient('my_session', os.getenv('API_ID'), os.getenv('API_HASH'))

# Список каналов
CHANNELS = [-1003895656743, -1003838037947]

@client.on(events.NewMessage(chats=CHANNELS))
async def handler(event):
    message = event.raw_text 
    
    if message and len(message) > 50: # Игнорируем слишком короткие сообщения
        print(f"Обработка сообщения из канала {event.chat_id}...")
        
        try:
            # Улучшенный промпт с упором на творческий апгрейд
            prompt = f"""
            Ты — дерзкий, глубокий автор Telegram-канала. Твоя задача: взять материал и превратить его в "виральный" лонгрид.
            
            ТВОЯ ЛИЧНОСТЬ:
            - Ты презираешь канцелярщину и банальности.
            - Ты ищешь парадоксы даже в простых новостях.
            - Ты пишешь так, будто рассказываешь секрет близкому другу.

            СТРУКТУРА ПОСТА:
            1. Заголовок: Цепляющий, провокационный, вызывающий любопытство.
            2. Хук: Первое предложение должно "бить в боль" или ломать стереотип читателя.
            3. Основная часть: Раскрой суть через парадоксальный угол зрения. Используй метафоры. Избегай длинных абзацев (макс. 4 строки).
            4. Финал: Заканчивай открытым вопросом, который вынудит читателя написать комментарий.

            Материал для обработки: {message}
            """

            # Использование system_instruction для закрепления роли
            response = client_ai.models.generate_content(
                model='models/gemini-2.5-flash-lite',
                contents=prompt,
                config={
                    'temperature': 0.75, # Высокая креативность
                    'top_p': 0.95,
                    'system_instruction': "Ты — элитный копирайтер, который пишет провокационно, глубоко и без воды. Твоя цель — заставить людей спорить и думать."
                }
            )
            
            # Отправка в "Избранное"
            await client.send_message('me', f"--- НОВЫЙ ПОСТ (из {event.chat_id}) ---\n\n{response.text}")
            
            await asyncio.sleep(5) 
            print("Готово!")
            
        except Exception as e:
            print(f"Ошибка при работе с ИИ: {e}")
            await client.send_message('me', f"Ошибка генерации: {e}")

client.start()
client.run_until_disconnected()