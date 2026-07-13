import time
from plyer import notification
from playsound import playsound

# 1. Аргументы называются правильно: title и message
def remind_me(title, message):
    notification.notify(
        title=title,
        message=message,
        app_name="Дисциплинатор3000",
        timeout=10
    )

print("Дисциплинатор3000 запущен и готов к работе!")

while True:
    time.sleep(1800) 
    
    # 2. Вызываем функцию с двумя аргументами через ЗАПЯТУЮ
    remind_me("Хватит лениться!", "ВРЕМЯ РАБОТАТЬ! Садись за дело.")
    
    # 3. Пытаемся играть звук
    try:
        playsound('cello.mp3')
    except Exception as e:
        print(f"Ой, звук не сработал: {e}")