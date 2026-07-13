try:
    from playwright_stealth import stealth_sync
    print("Успешно!")
except ImportError:
    try:
        from playwright_stealth import stealth
        print("Функция называется stealth")
    except ImportError:
        print("Ничего не найдено")