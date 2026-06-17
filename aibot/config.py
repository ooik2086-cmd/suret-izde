# -*- coding: utf-8 -*-
"""Боттың баптаулары — бәрі орта айнымалылары (env) арқылы өзгертіледі."""

import os


def _int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


# ── Негізгі кілттер ──
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "").strip()

# Тұрақты дерекқор (Render Postgres). Болмаса — жергілікті SQLite қолданылады.
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

# Үлкен видео жүктеу үшін (Pyrogram / MTProto) — my.telegram.org-тан.
TG_API_ID = _int("TG_API_ID", 0)
TG_API_HASH = os.environ.get("TG_API_HASH", "").strip()

# Render тегін жоспарда web-сервис $PORT-қа байлануды талап етеді.
PORT = _int("PORT", 8080)

# Боттың әкімшісі (статистика т.б. үшін, міндетті емес).
ADMIN_ID = _int("ADMIN_ID", 0)

# ── Тегін лимиттер (тәулігіне әр пайдаланушыға) ──
# МАҢЫЗДЫ: ақылы (Replicate) мүмкіндіктер әдепкіде 0 — олар тек сатып алынған
# кредитпен істейді (зиянсыз). Сурет тегін (Pollinations, шығын $0).
LIMITS = {
    "image":   _int("LIMIT_IMAGE", 100),
    "combine": _int("LIMIT_COMBINE", 0),
    "animate": _int("LIMIT_ANIMATE", 0),
    # 🎵 Музыка (вокал + аспап) — Replicate-те ақылы, сондықтан тәуліктік
    # тегін лимит АЗ (зиянды бақылау үшін). Керек болса LIMIT_MUSIC-пен өсіріңіз.
    "music":   _int("LIMIT_MUSIC", 1),
}

# ── Replicate модельдері (керек болса env-пен ауыстырыңыз) ──
MODELS = {
    "image":   os.environ.get("MODEL_IMAGE",   "black-forest-labs/flux-schnell"),
    # 2-3 суретті біріктіру/өңдеу (multi-image edit).
    "combine": os.environ.get("MODEL_COMBINE", "qwen/qwen-image-edit"),
    # Суреттегі кейіпкерді видеодағы қозғалыспен жандандыру (image + driving video).
    "animate": os.environ.get("MODEL_ANIMATE", "fofr/live-portrait"),
    # 🎵 Толық ән (вокал + музыка) мәтіннен. ACE-Step — кілтсіз үлгі видео
    # қажет етпейді (Suno-ға ең жақын ашық модель). Schema өзгерсе env-пен реттеңіз.
    "music":   os.environ.get("MODEL_MUSIC",   "lucataco/ace-step"),
}

# ── 🎵 Музыка моделінің кіріс өрістері (модель бойынша реттеуге болады) ──
# ACE-Step: tags (стиль) + lyrics (ән мәтіні) + duration (секунд).
MUSIC_TAGS_FIELD = os.environ.get("MUSIC_TAGS_FIELD", "tags")
MUSIC_LYRICS_FIELD = os.environ.get("MUSIC_LYRICS_FIELD", "lyrics")
MUSIC_DURATION_FIELD = os.environ.get("MUSIC_DURATION_FIELD", "duration")
MUSIC_DURATION = _int("MUSIC_DURATION", 60)  # ән ұзақтығы (секунд)

# "combine" моделіне суреттер қай өріспен берілетіні (модельге қарай реттеңіз).
COMBINE_IMAGE_FIELD = os.environ.get("COMBINE_IMAGE_FIELD", "image")

# "animate" моделінің кіріс өріс атаулары (модель бойынша өзгеше болуы мүмкін —
# env арқылы реттеңіз). fofr/live-portrait: face_image + driving_video.
ANIMATE_IMAGE_FIELD = os.environ.get("ANIMATE_IMAGE_FIELD", "face_image")
ANIMATE_VIDEO_FIELD = os.environ.get("ANIMATE_VIDEO_FIELD", "driving_video")

# Видеоны мүлдем өшіру керек болса: DISABLE_VIDEO=1
DISABLE_VIDEO = os.environ.get("DISABLE_VIDEO", "").strip() in ("1", "true", "yes")

# Сурет режимінде бір сұранымға қанша нұсқа жасалады (тегін, қатар жіберіледі).
IMAGE_VARIANTS = _int("IMAGE_VARIANTS", 3)

# ── Сурет форматтары (арақатынас → ені, биіктігі) ──
FORMATS = {
    "1x1":  (1024, 1024),
    "9x16": (768, 1344),
    "16x9": (1344, 768),
    "4x5":  (896, 1120),
    "3x4":  (864, 1152),
    "4x3":  (1152, 864),
}
FORMAT_ORDER = ["1x1", "9x16", "16x9", "4x5", "3x4", "4x3"]

# ── Telegram Stars пакеттері: (кредит_саны, жұлдыз_бағасы) ──
# 1 кредит = 1 ақылы жасау (видео/жандандыру/аватар/жаңарту).
# МАҢЫЗДЫ: бір кредит бағасы ең қымбат генерация құнынан (видео ~$0.5) жоғары
# болуы керек — сонда зиян болмайды. ~50⭐ ≈ $0.7–1.0.
PACKAGES = [(5, 300), (20, 1000), (50, 2200)]

# ── Жазылымдар: (күн_саны, жұлдыз_бағасы). Жазылым = ШЕКСІЗ СУРЕТ (видео емес). ──
# Сурет шығыны $0 болғандықтан, шексіз сурет — таза пайда.
# Шамамен курс: $1 ≈ 65 ⭐.  1 апта ≈ $2 (150⭐), 1 ай ≈ $10 (650⭐).
SUBSCRIPTIONS = [(7, 150), (30, 650)]

DEFAULT_LANG = os.environ.get("DEFAULT_LANG", "kz")

# SQLite дерекқор жолы (лимит/тіл сақтау үшін).
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "bot.db"))
