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

# Render тегін жоспарда web-сервис $PORT-қа байлануды талап етеді.
PORT = _int("PORT", 8080)

# Боттың әкімшісі (статистика т.б. үшін, міндетті емес).
ADMIN_ID = _int("ADMIN_ID", 0)

# ── Тегін лимиттер (тәулігіне әр пайдаланушыға) ──
# Видео қымбат болғандықтан әдепкіде аз. Бәрін env арқылы реттеуге болады.
LIMITS = {
    "image":   _int("LIMIT_IMAGE", 5),
    "video":   _int("LIMIT_VIDEO", 1),
    "restore": _int("LIMIT_RESTORE", 3),
    "avatar":  _int("LIMIT_AVATAR", 3),
    "animate": _int("LIMIT_ANIMATE", 1),
}

# ── Replicate модельдері (керек болса env-пен ауыстырыңыз) ──
MODELS = {
    "image":   os.environ.get("MODEL_IMAGE",   "black-forest-labs/flux-schnell"),
    "video":   os.environ.get("MODEL_VIDEO",   "minimax/video-01"),
    "restore": os.environ.get("MODEL_RESTORE", "tencentarc/gfpgan"),
    "avatar":  os.environ.get("MODEL_AVATAR",  "tencentarc/photomaker"),
    # Суреттегі кейіпкерді видеодағы қозғалыспен жандандыру (image + driving video).
    "animate": os.environ.get("MODEL_ANIMATE", "fofr/live-portrait"),
}

# "animate" моделінің кіріс өріс атаулары (модель бойынша өзгеше болуы мүмкін —
# env арқылы реттеңіз). fofr/live-portrait: face_image + driving_video.
ANIMATE_IMAGE_FIELD = os.environ.get("ANIMATE_IMAGE_FIELD", "face_image")
ANIMATE_VIDEO_FIELD = os.environ.get("ANIMATE_VIDEO_FIELD", "driving_video")

# Видеоны мүлдем өшіру керек болса: DISABLE_VIDEO=1
DISABLE_VIDEO = os.environ.get("DISABLE_VIDEO", "").strip() in ("1", "true", "yes")

# ── Telegram Stars пакеттері (генерация_саны, жұлдыз_бағасы) ──
# Лимит біткенде осы пакеттерді сатамыз. Stars-ты банксіз қабылдауға болады.
PACKAGES = [(10, 50), (50, 200), (250, 750)]

# ── Жазылымдар: (күн_саны, жұлдыз_бағасы). Жазылым кезінде шексіз қолдану. ──
# Шамамен курс: $1 ≈ 65 ⭐.  1 апта ≈ $2 (150⭐), 1 ай ≈ $10 (650⭐).
SUBSCRIPTIONS = [(7, 150), (30, 650)]

DEFAULT_LANG = os.environ.get("DEFAULT_LANG", "kz")

# SQLite дерекқор жолы (лимит/тіл сақтау үшін).
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "bot.db"))
