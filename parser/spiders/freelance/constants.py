# 3D-графика https://freelance.ru/project/search/pro?c=&c%5B%5D=577&q=&m=or&e=&a=0&a=1&v=0&v=1&f=&t=&o=0&o=1&b=&b%5B%5D=1&b%5B%5D=2&b%5B%5D=3
# Crypto/NFT https://freelance.ru/project/search/pro?c=&c%5B%5D=696&q=&m=or&e=&a=0&a=1&v=0&v=1&f=&t=&o=0&o=1&b=&b%5B%5D=1&b%5B%5D=2&b%5B%5D=3

# params = {
#     "c": "",
#     "c[]": [696],
#     "q": "",
#     "m": "or",
#     "e": "",
#     "a": [0, 1],
#     "v": [0, 1],
#     "f": "",
#     "t": "",
#     "o": [0, 1],
#     "b": "",
#     "b[]": [1, 2, 3]
# }

categories = {
    "3D графика": 577,
    "Арт / Иллюстрации / Анимация": 590,
    "Архитектура / предметы интерьера": 580,
    "Аутсорсинг / Консалтинг / Менеджмент": 133,
    "Бытовые услуги / Обучение": 663,
    "Видео": 565,
    "Графический дизайн": 40,
    "Инженерия": 186,
    "Интернет продвижение и реклама": 673,
    "Классическая реклама и маркетинг": 117,
    "Музыка / Звук": 89,
    "Направления отраслевого Дизайна": 716,
    "Переводы": 29,
    "Тексты": 124,
    "Фотография": 98
}

CATEGORIES = [{
    "title": "Разработка и IT",
    "code": "programming",
    "subcategories": [{
        "id": "116",
        "title": "Веб разработка",
        "code": "web-development",
    }, {
        "id": "696",
        "title": "Crypto/NFT",
        "code": "ai-blockchain",
    }, {
        "id": "724",
        "title": "Искусственный интеллект",
        "code": "ai-blockchain",
    }, {
        "id": "4",
        "title": "Программирование и IT",
        "code": "script-development",
    }]
}]

SUBCATEGORIES_REVERSE = {
    subcategory["id"]: subcategory["code"]
    for category in CATEGORIES
    for subcategory in category["subcategories"]
}
