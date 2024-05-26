SITES = [
    {
        "id": 85,
        "title": "Копирайтинг",
        "code": "writing",
    }, {
        "id": 3,
        "title": "Дизайн сайтов",
        "code": "design",
    }, {
        "id": 164,
        "title": "Контент-менеджер",
        "code": "writing",
    }, {
        "id": 84,
        "title": "Менеджер проектов",
        "code": "consulting",
    }, {
        "id": 502,
        "title": "Редизайн сайтов",
        "code": "design",
    }, {
        "id": 470,
        "title": "Пользовательские соглашения",
        "code": "consulting",
    }
]

CATEGORIES = [{
    "title": "Разработка и IT",
    "code": "programming",
    "subcategories": [{
        "id": 37,
        "title": "Веб-программирование",
        "code": "web-development",
    }, {
        "id": 1,
        "title": "Прикладное программирование",
        "code": "desktop-development",
    }, {
        "id": 279,
        "title": "Разработка Чат-ботов",
        "code": "script-development",
    }, {
        "id": 225,
        "title": "Google Android",
        "code": "mobile-development",
    }, {
        "id": 97,
        "title": "1С-программирование",
        "code": "other-development",
    }, {
        "id": 280,
        "title": "Парсинг данных",
        "code": "script-development",
    }, {
        "id": 5,
        "title": "Базы данных",
        "code": "databases-development",
    }, {
        "id": 226,
        "title": "iOS",
        "code": "mobile-development",
    }, {
        "id": 297,
        "title": "Создание скриптов",
        "code": "script-development",
    }, {
        "id": 2,
        "title": "Системное программирование",
        "code": "desktop-development",
    }, {
        "id": 222,
        "title": "Разработка CRM и ERP",
        "code": "other-development",
    }, {
        "id": 6,
        "title": "Программирование для сотовых телефонов и КПК",
        "code": "mobile-development",
    }, {
        "id": 296,
        "title": "Машинное обучение",
        "code": "ai-blockchain",
    }, {
        "id": 221,
        "title": "Плагины/Сценарии/Утилиты",
        "code": "script-development",
    }, {
        "id": 223,
        "title": "Интерактивные приложения",
        "code": "web-development",
    }, {
        "id": 161,
        "title": "Встраиваемые системы",
        "code": "other-development",
    }, {
        "id": 278,
        "title": "Blockchain",
        "code": "ai-blockchain",
    }, {
        "id": 229,
        "title": "Прототипирование",
        "code": "other-development",
    }, {
        "id": 473,
        "title": "Laravel",
        "code": "web-development",
    }, {
        "id": 474,
        "title": "Vue",
        "code": "web-development",
    }, {
        "id": 355,
        "title": "Yii",
        "code": "web-development",
    }, {
        "id": 9,
        "title": "Веб-программирование",
        "code": "web-development",
    }, {
        "id": 27,
        "title": "Сайт «под ключ»",
        "code": "web-development",
    }, {
        "id": 8,
        "title": "Верстка",
        "code": "web-development",
    }, {
        "id": 282,
        "title": "Тильда",
        "code": "web-development",
    }, {
        "id": 276,
        "title": "Лендинги",
        "code": "web-development",
    }, {
        "id": 81,
        "title": "QA (тестирование)",
        "code": "testing-audit",
    }, {
        "id": 217,
        "title": "Интернет-магазины",
        "code": "web-development",
    }, {
        "id": 275,
        "title": "WordPress",
        "code": "web-development",
    }, {
        "id": 220,
        "title": "Доработка сайтов",
        "code": "web-development",
    }, {
        "id": 86,
        "title": "CMS (системы управления)",
        "code": "web-development",
    }, {
        "id": 218,
        "title": "Проектирование",
        "code": "web-development",
    }, {
        "id": 281,
        "title": "1С Битрикс",
        "code": "web-development",
    }, {
        "id": 307,
        "title": "Zero-coding",
        "code": "web-development",
    }, {
        "id": 349,
        "title": "React",
        "code": "web-development",
    }, {
        "id": 219,
        "title": "Юзабилити-анализ",
        "code": "testing-audit",
    }, {
        "id": 72,
        "title": "Wap/PDA-сайты",
        "code": "web-development",
    }, {
        "id": 87,
        "title": "Флеш-сайты",
        "code": "web-development",
    }, {
        "id": 347,
        "title": "Laravel",
        "code": "web-development",
    }, {
        "id": 348,
        "title": "Vue",
        "code": "web-development",
    }, {
        "id": 350,
        "title": "Node",
        "code": "web-development",
    }, {
        "id": 353,
        "title": "Joomla",
        "code": "web-development",
    }, {
        "id": 443,
        "title": "Webflow",
        "code": "web-development",
    }, {
        "id": 351,
        "title": "OpenCart",
        "code": "web-development",
    }, {
        "id": 352,
        "title": "MODx",
        "code": "web-development",
    }, {
        "id": 354,
        "title": "Magento",
        "code": "web-development",
    }, {
        "id": 475,
        "title": "Yii",
        "code": "web-development",
    }],
}]

SUBCATEGORIES_REVERSE = {
    subcategory["id"]: subcategory["code"]
    for category in CATEGORIES
    for subcategory in category["subcategories"]
}
