TEXTS = {
    "uz": {
        "welcome": "Assalomu alaykum! Universal Media botiga xush kelibsiz.",
        "choose": "Kerakli bo‘limni tanlang:",
        "media": "Media havolasi",
        "music": "Musiqa qidirish",
        "language": "Tilni tanlash",
        "language_saved": "Til o‘zgartirildi.",
        "media_help": "Ommaviy va siz foydalanishga ruxsat olgan media havolasini yuboring. Hozircha havola tekshiruvi bosqichi ishlab chiqilmoqda.",
        "music_help": "Qo‘shiq nomi yoki ijrochi nomini yuboring. Musiqa qidirish xizmati keyingi bosqichda ulanadi.",
        "admin_only": "Bu buyruq faqat administrator uchun.",
        "unknown": "Bu bo‘lim hali ishlab chiqilmoqda.",
    },
    "ru": {
        "welcome": "Здравствуйте! Добро пожаловать в Universal Media.",
        "choose": "Выберите нужный раздел:",
        "media": "Ссылка на медиа",
        "music": "Поиск музыки",
        "language": "Выбрать язык",
        "language_saved": "Язык изменён.",
        "media_help": "Отправьте публичную ссылку на контент, которым вы имеете право пользоваться. Проверка ссылок пока находится в разработке.",
        "music_help": "Отправьте название песни или имя исполнителя. Поиск музыки будет подключён на следующем этапе.",
        "admin_only": "Эта команда доступна только администратору.",
        "unknown": "Этот раздел пока находится в разработке.",
    },
    "en": {
        "welcome": "Hello! Welcome to Universal Media.",
        "choose": "Choose a section:",
        "media": "Media link",
        "music": "Music search",
        "language": "Choose language",
        "language_saved": "Language updated.",
        "media_help": "Send a public link to content you are authorized to use. Link processing is currently under development.",
        "music_help": "Send a song title or artist name. Music search will be connected in a later milestone.",
        "admin_only": "This command is for the administrator only.",
        "unknown": "This section is still under development.",
    },
}


def get_text(language: str, key: str) -> str:
    selected = language if language in TEXTS else "uz"
    return TEXTS[selected].get(key, TEXTS["uz"].get(key, key))
