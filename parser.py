import sqlite3
import re
import time
import random
import logging
import requests
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
 
# ─── Настройки ────────────────────────────────────────────────────────────────
TOKEN   = "8959277530:AAFMyFpuMErFFYwO83a36wiIQaEB3eKxoOg"          # Telegram bot token
CHAT_ID = "6683544194"          # Telegram chat id
DB_NAME = "monitor.db"
DISCOUNT_THRESHOLD = 20   # % снижения цены для уведомления
PAGE_DELAY  = (4, 8)      # Увеличенная случайная пауза между страницами (сек)
SCROLL_STEP = 2000        # пикселей за один прокрут
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)
 
# ─── Telegram ─────────────────────────────────────────────────────────────────
def send_telegram(text: str) -> None:
    """Отправляет сообщение в Telegram. Молча логирует ошибки."""
    if not TOKEN or not CHAT_ID:
        log.warning("Telegram TOKEN или CHAT_ID не заданы — уведомление пропущено.")
        return
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            params={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        r.raise_for_status()
    except Exception as e:
        log.error(f"Telegram error: {e}")
 
 
# ─── База данных ──────────────────────────────────────────────────────────────
def init_db(conn: sqlite3.Connection) -> None:
    """Создаёт таблицы с правильной уникальностью по product_id."""
    cur = conn.cursor()
 
    # Исправлено: PRIMARY KEY теперь только по product_id. 
    # Рекламный товар из другой категории обновит существующий, а не создаст дубль!
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id  TEXT PRIMARY KEY,
            name        TEXT    NOT NULL,
            price       INTEGER NOT NULL,
            old_price   INTEGER,
            link        TEXT,
            category    TEXT    NOT NULL,
            updated_at  TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)
 
    # История изменений цены
    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id  TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            price       INTEGER NOT NULL,
            recorded_at TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)
 
    conn.commit()
 
 
def save_product(
    conn: sqlite3.Connection,
    product_id: str,
    name: str,
    price: int,
    old_price: int | None,
    link: str,
    category: str,
) -> None:
    """
    Сохраняет товар. Пишет изменения в историю цен.
    Отправляет уведомление, если цена упала по сравнению с прошлой в БД, 
    ИЛИ если Пром прямо сейчас отдает товар со скидкой на сайте (через old_price).
    """
    cur = conn.cursor()
 
    # Читаем предыдущую цену из БД перед обновлением
    cur.execute(
        "SELECT price FROM products WHERE product_id = ?",
        (product_id,),
    )
    row = cur.fetchone()
    prev_db_price: int | None = row[0] if row else None
 
    # Записываем/обновляем товар
    cur.execute(
        """
        INSERT INTO products (product_id, name, price, old_price, link, category, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now','localtime'))
        ON CONFLICT(product_id) DO UPDATE SET
            name       = excluded.name,
            price      = excluded.price,
            old_price  = excluded.old_price,
            link       = excluded.link,
            category   = excluded.category,
            updated_at = excluded.updated_at
        """,
        (product_id, name, price, old_price, link, category),
    )
 
    # Запись в историю: если товара не было ВООБЩЕ или изменилась цена
    if prev_db_price is None or prev_db_price != price:
        cur.execute(
            "INSERT INTO price_history (product_id, category, price) VALUES (?, ?, ?)",
            (product_id, category, price),
        )
 
    # ── Логика уведомлений о скидках ──
    msg = None
 
    # Вариант А: Цена упала по сравнению с прошлым запуском парсера
    if prev_db_price and prev_db_price > 0 and price < prev_db_price:
        drop_pct = (prev_db_price - price) / prev_db_price * 100
        if drop_pct >= DISCOUNT_THRESHOLD:
            msg = (
                f"📉 <b>Снижение цены (динамика базы) на {drop_pct:.1f}%!</b>\n"
                f"{name}\n"
                f"Было в БД: <s>{prev_db_price} ₴</s> → Стало: <b>{price} ₴</b>\n"
                f'<a href="{link}">Открыть товар</a>'
            )
 
    # Вариант Б: Товар найден впервые, но на сайте на него уже висит зачеркнутая старая цена
    elif prev_db_price is None and old_price and old_price > price:
        site_drop_pct = (old_price - price) / old_price * 100
        if site_drop_pct >= DISCOUNT_THRESHOLD:
            msg = (
                f"🏷️ <b>Обнаружена скидка на сайте: {site_drop_pct:.1f}%!</b>\n"
                f"{name}\n"
                f"Старая цена сайта: <s>{old_price} ₴</s> → Текущая: <b>{price} ₴</b>\n"
                f'<a href="{link}">Открыть товар</a>'
            )
 
    # Отправляем, если сработал один из триггеров
    if msg:
        send_telegram(msg)
        log.info(f" 💰 Отправлено уведомление о скидке для '{name[:40]}...'")
 
 
# ─── Playwright helpers ───────────────────────────────────────────────────────
def build_browser(p):
    """Запускает Chromium с anti-bot настройками."""
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
        ],
    )
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1366, "height": 768},
        locale="uk-UA",
        timezone_id="Europe/Kiev",
        extra_http_headers={
            "Accept-Language": "uk-UA,uk;q=0.9,ru;q=0.8",
        },
    )
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = { runtime: {} };
    """)
    return browser, context
 
 
def scroll_page(page) -> None:
    """Плавная прокрутка вниз для подгрузки lazy-load элементов."""
    for _ in range(5):
        page.mouse.wheel(0, SCROLL_STEP)
        page.wait_for_timeout(random.randint(700, 1200))
    try:
        page.wait_for_load_state("networkidle", timeout=4000)
    except PlaywrightTimeout:
        pass
 
 
def extract_product_id(href: str | None) -> str:
    """Извлекает числовой ID товара из URL."""
    if not href:
        return ""
    m = re.search(r"/p(\d+)-", href)
    return m.group(1) if m else href
 
 
def parse_price(text: str) -> int | None:
    """
    Парсит цену: '1 057,00 грн' -> 1057.
    """
    # Убираем все, кроме цифр, запятой и точки
    clean_text = "".join(filter(lambda x: x.isdigit() or x in (',', '.'), text))
    
    if not clean_text:
        return None
    
    # Заменяем запятую на точку для корректного перевода в число
    clean_text = clean_text.replace(',', '.')
    
    # Превращаем в float, чтобы корректно обработать копейки
    try:
        price_float = float(clean_text)
        # Если цена выглядит как 105700 (из-за копеек), делим на 100
        # Но осторожно: нужно понять, это реальные 1000 грн или 10 грн с копейками
        if price_float > 10000 and (price_float % 100 == 0):
            price_float = price_float / 100
            
        return int(price_float)
    except ValueError:
        return None
 
 
# ─── Парсинг страницы ─────────────────────────────────────────────────────────
def parse_page(page, conn: sqlite3.Connection, category: str) -> int:
    """Собирает все товары с текущей страницы."""
    count = 0
    items = page.locator('[data-qaid="product_block"]').all()
    log.info(f"    Найдено блоков товаров: {len(items)}")
 
    for item in items:
        try:
            # Название
            name_loc = item.locator('[data-qaid="product_name"]')
            if not name_loc.count():
                continue
            name = name_loc.inner_text(timeout=3000).strip()
            if not name:
                continue
 
            # Текущая цена
            price_loc = item.locator('[data-qaid="product_price"]').first
            if not price_loc.count():
                continue
            price = parse_price(price_loc.inner_text(timeout=3000))
            if price is None:
                continue
 
            # Старая цена (зачёркнутая)
            old_price: int | None = None
            old_price_loc = item.locator('[data-qaid="old_price"]')
            if old_price_loc.count():
                old_price = parse_price(old_price_loc.inner_text(timeout=2000))
 
            # Ссылка и product_id
            a_loc = item.locator('a[href*="/p"]').first
            href = a_loc.get_attribute("href", timeout=3000) if a_loc.count() else None
            link = ("https://prom.ua" + href) if href and not href.startswith("http") else (href or "")
            product_id = extract_product_id(href)
 
            if not product_id:
                continue
 
            save_product(conn, product_id, name, price, old_price, link, category)
            count += 1
 
        except PlaywrightTimeout:
            log.debug("    Timeout при чтении элемента — пропускаем")
        except Exception as e:
            log.warning(f"    Ошибка товара: {type(e).__name__}: {e}")
 
    conn.commit()
    return count
 
 
# ─── Пагинация ────────────────────────────────────────────────────────────────
def next_page(page) -> bool:
    """Кликает «следующая страница» с эмуляцией человеческого поведения."""
    try:
        btn = page.locator('[data-qaid="next_page"]')
        btn.wait_for(state="visible", timeout=5000)
        if not btn.is_enabled():
            return False
 
        prev_url = page.url
        btn.click()
 
        try:
            page.wait_for_url(lambda u: u != prev_url, timeout=12000)
        except PlaywrightTimeout:
            log.info("  URL не изменился — последняя страница.")
            return False
 
        page.wait_for_selector('[data-qaid="product_block"]', timeout=15000)
        
        # Исправлено: увеличен таймаут чтения страницы для очеловечивания бота
        page.wait_for_timeout(random.randint(3000, 6000))
        return True
 
    except PlaywrightTimeout:
        return False
    except Exception as e:
        log.warning(f"  Ошибка пагинации: {e}")
        return False
 
 
# ─── Основной цикл ────────────────────────────────────────────────────────────
def run_bot() -> None:
    with open("search.txt", "r", encoding="utf-8") as f:
        search_terms = [ln.strip() for ln in f if ln.strip()]
 
    if not search_terms:
        log.error("search.txt пуст!")
        return
 
    conn = sqlite3.connect(DB_NAME)
    init_db(conn)
 
    grand_total = 0
 
    with sync_playwright() as p:
        browser, context = build_browser(p)
        page = context.new_page()
 
        for term in search_terms:
            log.info(f"\n{'='*55}")
            log.info(f"Запрос: {term}")
 
            url = f"https://prom.ua/search?{urlencode({'search_term': term})}"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_selector('[data-qaid="product_block"]', timeout=15000)
            except PlaywrightTimeout:
                log.warning(f"  Товары не найдены для: {term}")
                continue
 
            page_num   = 1
            term_total = 0
 
            while True:
                log.info(f"  Страница {page_num} | {page.url}")
                scroll_page(page)
 
                found = parse_page(page, conn, term)
                term_total += found
                log.info(f"  Обработано блоков: {found} (накопительный итог: {term_total})")
 
                if not next_page(page):
                    log.info("  Последняя страница — переходим к следующему запросу.")
                    break
 
                page_num += 1
                time.sleep(random.uniform(*PAGE_DELAY))
 
            grand_total += term_total
            log.info(f"'{term}': {term_total} проходов карточек, {page_num} стр.")
 
        context.close()
        browser.close()
 
    conn.close()
    summary = f"✅ Сбор завершён!\nЗапросов: {len(search_terms)}\nВсего уникальных строк в базе проверишь в DB Browser."
    send_telegram(summary)
    log.info(f"\n{summary}")
 
 
if __name__ == "__main__":
    run_bot()