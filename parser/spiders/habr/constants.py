CATEGORIES = [{
    "title": "Разработка и IT",
    "code": "programming",
    "subcategories": [{
        "id": "development_all_inclusive",
        "title": "Сайты «под ключ»",
        "code": "web-development",
    }, {
        "id": "development_backend",
        "title": "Бэкенд",
        "code": "web-development",
    }, {
        "id": "development_frontend",
        "title": "Фронтенд",
        "code": "web-development",
    }, {
        "id": "development_prototyping",
        "title": "Прототипирование",
        "code": "other-development",
    }, {
        "id": "development_ios",
        "title": "iOS",
        "code": "mobile-development",
    }, {
        "id": "development_android",
        "title": "Android",
        "code": "mobile-development",
    }, {
        "id": "development_desktop",
        "title": "Десктопное ПО",
        "code": "desktop-development",
    }, {
        "id": "development_bots",
        "title": "Боты и парсинг данных",
        "code": "script-development",
    }, {
        "id": "development_games",
        "title": "Разработка игр",
        "code": "game-development",
    }, {
        "id": "development_1c_dev",
        "title": "1С-программирование",
        "code": "other-development",
    }, {
        "id": "development_scripts",
        "title": "Скрипты и плагины",
        "code": "script-development",
    }, {
        "id": "development_voice_interfaces",
        "title": "Голосовые интерфейсы",
        "code": "other-development",
    }, {
        "id": "development_other",
        "title": "Разное",
        "code": "other-development",
    }, {
        "id": "testing_sites",
        "title": "Тестирование Сайты",
        "code": "testing-audit",
    }, {
        "id": "testing_mobile",
        "title": "Тестирование Мобайл",
        "code": "testing-audit",
    }, {
        "id": "testing_software",
        "title": "Тестирование Софт",
        "code": "testing-audit",
    }, {
        "id": "admin_servers",
        "title": "Серверы",
        "code": "servers-hosting",
    }, {
        "id": "admin_network",
        "title": "Компьютерные сети",
        "code": "servers-hosting",
    }, {
        "id": "admin_databases",
        "title": "Базы данных",
        "code": "databases-development",
    }, {
        "id": "admin_security",
        "title": "Защита ПО и безопасность",
        "code": "servers-hosting",
    }, {
        "id": "admin_other",
        "title": "Администрирование Разное",
        "code": "servers-hosting",
    }]
}]

SUBCATEGORIES_REVERSE = {
    subcategory["id"]: subcategory["code"]
    for category in CATEGORIES
    for subcategory in category["subcategories"]
}
