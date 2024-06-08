CATEGORIES = [{
    "id": 11,
    "title": "Разработка и IT",
    "code": "programming",
    "subcategories": [{
        "id": 38,
        "title": "Доработка и настройка сайта",
        "code": "web-development",
    }, {
        "id": 79,
        "title": "Верстка",
        "code": "web-development",
    }, {
        "id": 37,
        "title": "Создание сайта",
        "code": "web-development",
    }, {
        "id": 41,
        "title": "Скрипты и боты",
        "code": "script-development",
    }, {
        "id": 39,
        "title": "Мобильные приложения",
        "code": "mobile-development",
    }, {
        "id": 40,
        "title": "Игры",
        "code": "game-development",
    }, {
        "id": 80,
        "title": "Десктоп программирование",
        "code": "desktop-development",
    }, {
        "id": 255,
        "title": "Сервера и хостинг",
        "code": "servers-hosting",
    }, {
        "id": 81,
        "title": "Юзабилити, тесты и помощь",
        "code": "testing-audit",
    }]
},

]

SUBCATEGORIES_REVERSE = {
    subcategory["id"]: subcategory["code"]
    for category in CATEGORIES
    for subcategory in category["subcategories"]
}
