import os
import time
import requests
from playwright.sync_api import sync_playwright

# Настройки
SAVE_DIR = "downloaded_images"
QUERY = "Adidas"

# Создаем папку для картинок, если её нет
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def download_image(url, index):
    try:
        response = requests.get(url, timeout=10)
        file_path = os.path.join(SAVE_DIR, f"image_{index}.jpg")
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"Успешно сохранено: {file_path}")
    except Exception as e:
        print(f"Ошибка при скачивании {url}: {e}")

def run_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        print(f"Ищем в Pinterest: {QUERY}...")
        page.goto(f"https://www.pinterest.com/search/pins/?q={QUERY}")
        
        # Прокрутка для подгрузки контента
        for i in range(3):
            page.mouse.wheel(0, 2000)
            time.sleep(2)
        
        # Собираем изображения
        # Замените цикл перебора картинок в вашем коде на этот:
        images = page.query_selector_all('img')
        count = 0
        for img in images:
            # Получаем атрибут src
            src = img.get_attribute('src')
            
            # Проверяем, что ссылка валидная и это картинка пина
            if src and '236x' in src:
                # ХАК: заменяем '236x' на 'originals' для получения высокого качества
                high_quality_src = src.replace('236x', 'originals')
                
                print(f"Скачиваю в высоком качестве: {high_quality_src}")
                download_image(high_quality_src, count)
                count += 1
        
        print(f"Завершено. Всего скачано: {count} изображений.")
        browser.close()

if __name__ == "__main__":
    run_scraper()