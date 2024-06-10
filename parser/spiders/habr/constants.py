CATEGORIES = [{
    "title": "Разработка и IT",
    "code": "programming",
    "subcategories": [
        {"id": "development_all_inclusive", "title": "Сайты «под ключ»", "code": "web-development"},
        {"id": "development_backend", "title": "Бэкенд", "code": "web-development"},
        {"id": "development_frontend", "title": "Фронтенд", "code": "web-development"},
        {"id": "development_prototyping", "title": "Прототипирование", "code": "other-development"},
        {"id": "development_ios", "title": "iOS", "code": "mobile-development"},
        {"id": "development_android", "title": "Android", "code": "mobile-development"},
        {"id": "development_desktop", "title": "Десктопное ПО", "code": "desktop-development"},
        {"id": "development_bots", "title": "Боты и парсинг данных", "code": "script-development"},
        {"id": "development_games", "title": "Разработка игр", "code": "game-development"},
        {"id": "development_1c_dev", "title": "1С-программирование", "code": "other-development"},
        {"id": "development_scripts", "title": "Скрипты и плагины", "code": "script-development"},
        {"id": "development_voice_interfaces", "title": "Голосовые интерфейсы", "code": "web-development"},
        {"id": "development_other", "title": "Разное", "code": "other-development"},
        {"id": "testing_sites", "title": "Тестирование Сайты", "code": "testing-audit"},
        {"id": "testing_mobile", "title": "Тестирование Мобайл", "code": "testing-audit"},
        {"id": "testing_software", "title": "Тестирование Софт", "code": "testing-audit"},
        {"id": "admin_servers", "title": "Серверы", "code": "servers-hosting"},
        {"id": "admin_network", "title": "Компьютерные сети", "code": "servers-hosting"},
        {"id": "admin_databases", "title": "Базы данных", "code": "databases-development"},
        {"id": "admin_security", "title": "Защита ПО и безопасность", "code": "web-development"},
        {"id": "admin_other", "title": "Администрирование Разное", "code": "servers-hosting"},
    ],
}, {
    "title": "Дизайн и графика",
    "code": "design",
    "subcategories": [
        {"id": "design_sites", "title": "Сайты", "code": "design-web-mobile"},
        {"id": "design_landings", "title": "Лендинги", "code": "design-web-mobile"},
        {"id": "design_logos", "title": "Логотипы", "code": "design-branding"},
        {"id": "design_illustrations", "title": "Рисунки и иллюстрации", "code": "design-art"},
        {"id": "design_mobile", "title": "Мобильные приложения", "code": "design-web-mobile"},
        {"id": "design_icons", "title": "Иконки", "code": "design-web-mobile"},
        {"id": "design_polygraphy", "title": "Полиграфия", "code": "design-layout"},
        {"id": "design_banners", "title": "Баннеры", "code": "design-outdoor"},
        {"id": "design_graphics", "title": "Векторная графика", "code": "design-art"},
        {"id": "design_corporate_identity", "title": "Фирменный стиль", "code": "design-branding"},
        {"id": "design_presentations", "title": "Презентации", "code": "design-presentations"},
        {"id": "design_modeling", "title": "3D", "code": "design-3d-graphics"},
        {"id": "design_animation", "title": "Анимация", "code": "design-art"},
        {"id": "design_photo", "title": "Обработка фото", "code": "design-art"},
        {"id": "design_other", "title": "Разное", "code": "design-other"},
    ],
}, {
    "title": "Маркетинг и реклама",
    "code": "marketing",
    "subcategories": [
        {"id": "marketing_smm", "title": "SMM", "code": "marketing-smm"},
        {"id": "marketing_seo", "title": "SEO", "code": "marketing-seo"},
        {"id": "marketing_context", "title": "Контекстная реклама", "code": "marketing-ppc"},
        {"id": "marketing_email", "title": "E-mail маркетинг", "code": "marketing-marketing"},
        {"id": "marketing_research", "title": "Исследования рынка и опросы", "code": "marketing-other"},
        {"id": "marketing_sales", "title": "Продажи и генерация лидов", "code": "marketing-marketing"},
        {"id": "marketing_pr", "title": "PR-менеджмент", "code": "marketing-pr"},
        {"id": "marketing_other", "title": "Разное", "code": "marketing-other"},
    ],
}]

SUBCATEGORIES_REVERSE = {
    subcategory["id"]: subcategory["code"]
    for category in CATEGORIES
    for subcategory in category["subcategories"]
}
