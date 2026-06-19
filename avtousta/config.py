# -*- coding: utf-8 -*-
"""AvtoUsta боттың баптаулары — бәрі орта айнымалылары (env) арқылы өзгертіледі.

AvtoUsta — автокөлік иелері мен автожөндеу шеберлерін байланыстыратын
маркетплейс (Қазақстан). Екі рөл: 🙋 Клиент (көлік иесі) және 🛠 Шебер/СТО.
"""

import os


def _int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


# ── Негізгі кілттер ──
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

# Тұрақты дерекқор (Render Postgres). Болмаса — жергілікті SQLite қолданылады.
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

# Render тегін жоспарда web-сервис $PORT-қа байлануды талап етеді.
PORT = _int("PORT", 8080)

# Боттың әкімшісі (модерация/верификация хабарламалары үшін, міндетті емес).
ADMIN_ID = _int("ADMIN_ID", 0)

DEFAULT_LANG = os.environ.get("DEFAULT_LANG", "kz")

# SQLite дерекқор жолы (Postgres болмаса).
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "avtousta.db"))


# ── Рөлдер ──
ROLE_CLIENT = "client"
ROLE_MASTER = "master"

# ── Шебер түрі (ғимарат/мобильдік) ──
# key, emoji, kz, ru
MASTER_TYPES = [
    ("sto",    "🏢", "СТО / бокс бар",            "СТО / есть бокс"),
    ("garage", "🏠", "Үй гаражы",                 "Домашний гараж"),
    ("mobile", "🚐", "Мобильді (барып жөндейді)", "Выездной мастер"),
]
MASTER_TYPE_KEYS = [k for k, *_ in MASTER_TYPES]


# ── Мамандық санаттары (автожөндеу) ──
# key, emoji, kz, ru
CATEGORIES = [
    ("motor",        "🔧", "Қозғалтқыш (мотор)",       "Двигатель (мотор)"),
    ("electric",     "⚡", "Электроника / электрик",   "Электроника / электрик"),
    ("body",         "🚗", "Кузов / бояу",             "Кузов / покраска"),
    ("suspension",   "🔩", "Жүріс бөлігі (ходовая)",   "Ходовая часть"),
    ("transmission", "⚙️", "Беріліс қорабы (КПП)",     "Коробка передач (КПП)"),
    ("diagnostics",  "💻", "Компьютерлік диагностика", "Компьютерная диагностика"),
    ("maintenance",  "🛢", "Май ауыстыру / ТО",        "Замена масла / ТО"),
    ("tires",        "🛞", "Шиномонтаж / дөңгелек",    "Шиномонтаж / шины"),
    ("ac",           "❄️", "Кондиционер",              "Кондиционер"),
    ("evac",         "🚛", "Эвакуатор",                "Эвакуатор"),
]
CATEGORY_KEYS = [k for k, *_ in CATEGORIES]


def cat_label(lang, key):
    for k, emoji, kz, ru in CATEGORIES:
        if k == key:
            return "%s %s" % (emoji, kz if lang == "kz" else ru)
    return key


def mtype_label(lang, key):
    for k, emoji, kz, ru in MASTER_TYPES:
        if k == key:
            return "%s %s" % (emoji, kz if lang == "kz" else ru)
    return key


# ── Монетизация (зиянсыз; Telegram Stars) ──
# Тапсырыс комиссиясы (%) — кейінгі кезеңде сәтті тапсырыстан алынады.
COMMISSION_PCT = _int("COMMISSION_PCT", 7)
# Шебер жазылымы: (күн, жұлдыз). Жазылым = шектеусіз тапсырыс + белсенді профиль.
MASTER_SUBSCRIPTIONS = [(30, 650), (90, 1700)]
# TOP/жарнама (профильді жоғары шығару): (күн, жұлдыз).
PROMOTIONS = [(7, 300), (30, 1000)]

# Іздеуде бір бетте қанша шебер көрсетіледі.
SEARCH_PAGE_SIZE = _int("SEARCH_PAGE_SIZE", 5)
