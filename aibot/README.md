# 🤖 AI-генератор Telegram бот

Адамдар ботқа жазады → бот AI арқылы **сурет / видео / фото жаңарту / аватар** жасап береді.
Қазір **тегін лимитпен** (тәулігіне әр пайдаланушыға) жұмыс істейді; кейін төлем (Telegram Stars) қосуға дайын.

- 🇰🇿 Қазақша / 🇷🇺 Орысша интерфейс
- Бэкенд: **Replicate** (нақты AI). Токен болмаса — **демо режим** (бірден сынауға).
- Хостинг: Render тегін web-сервис (long-polling + health сервер қатар).

---

## 1. Жергілікті іске қосу

```bash
cd aibot
pip install -r requirements.txt

export BOT_TOKEN=123456:ABC...          # @BotFather-дан
export REPLICATE_API_TOKEN=r8_...       # міндетті емес (болмаса демо режим)
python bot.py
```

`BOT_TOKEN` жоқ болса бот ескертіп тоқтайды. `REPLICATE_API_TOKEN` жоқ болса —
демо режимде placeholder сурет қайтарады (логиканы тегін тексеру үшін).

### Токендерді қайдан аламын

| Не керек | Қайдан |
|---|---|
| `BOT_TOKEN` | Telegram-да [@BotFather](https://t.me/BotFather) → `/newbot` |
| `REPLICATE_API_TOKEN` | https://replicate.com/account/api-tokens |

---

## 2. Баптаулар (env)

| Айнымалы | Әдепкі | Сипат |
|---|---|---|
| `BOT_TOKEN` | — | **Міндетті.** Telegram бот токені |
| `REPLICATE_API_TOKEN` | — | Replicate кілті (жоқ болса демо) |
| `LIMIT_IMAGE` | 5 | Тәуліктік тегін сурет лимиті |
| `LIMIT_VIDEO` | 1 | Тәуліктік тегін видео лимиті |
| `LIMIT_RESTORE` | 3 | Тәуліктік фото жаңарту лимиті |
| `LIMIT_AVATAR` | 3 | Тәуліктік аватар лимиті |
| `DISABLE_VIDEO` | — | `1` болса видео мүлдем өшеді (шығынды бақылау) |
| `MODEL_IMAGE` | `black-forest-labs/flux-schnell` | Replicate моделі |
| `MODEL_VIDEO` | `minimax/video-01` | Replicate моделі |
| `MODEL_RESTORE` | `tencentarc/gfpgan` | Replicate моделі |
| `MODEL_AVATAR` | `tencentarc/photomaker` | Replicate моделі |
| `DEFAULT_LANG` | `kz` | Әдепкі тіл (`kz`/`ru`) |
| `PORT` | 8080 | Render үшін health сервер порты |
| `DB_PATH` | `aibot/bot.db` | SQLite жолы |

> Модель кірістерінің схемасы Replicate-те өзгеруі мүмкін. Қате шықса,
> `MODEL_*` айнымалысын басқа модельге ауыстырыңыз немесе `providers.py`
> ішіндегі `_build_input` функциясын реттеңіз.

---

## 3. Render-ге деплой (тегін)

Бот — long-polling, бірақ Render тегін жоспарда тек **web-сервис** болады.
Сондықтан бот polling-пен қатар `$PORT`-та кішкентай health сервер ашады.

Render → **New Web Service** → осы репозиторий → баптаулар:

- **Root Directory:** `aibot`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python bot.py`
- **Environment:** `BOT_TOKEN`, `REPLICATE_API_TOKEN` (және қаласаңыз лимиттер)

Тегін сервис ұйықтап қалмас үшін `../.github/workflows/keepalive.yml`
сияқты ping қосуға болады (health эндпойнт: `/`).

---

## 4. Қалай ақша табады

1. **Тегін лимит** — әркім күніне бірнеше тегін генерация жасайды (тарту үшін).
2. **Лимит бітсе** — бот «төлем жақында» дейді. Келесі қадам: **Telegram Stars**
   (банк-эквайринг қажет емес, KZ-да жұмыс істейді) арқылы пакет сату:
   мыс. «100 сурет = N жұлдыз». Stars-ты ақшаға айналдыруға болады.
3. **Маржа** — Replicate шығыны (мыс. flux-schnell ~бір сурет арзан) мен
   сату бағасының айырмасы.

> Төлем коды әлі қосылмаған (сіздің таңдауыңыз — «алдымен тегін»).
> Дайын болғанда `aiogram` Telegram Stars (`XTR` валютасы, `send_invoice`)
> арқылы оңай жалғанады — лимит логикасы соған дайын тұр.

---

## 5. Сынақтар

```bash
cd ..              # репозиторий түбірі
python -m pytest -q
```

`aibot/tests/test_core.py` — i18n, лимиттер, провайдер логикасын Telegram/желісіз
тексереді. CI (`.github/workflows/test.yml`) әр push сайын жүргізеді.

---

## Файлдар

| Файл | Не үшін |
|---|---|
| `bot.py` | aiogram хендлерлері, мәзір, генерация ағыны, health сервер |
| `providers.py` | Replicate / Demo провайдерлері (ауыстырмалы «ми») |
| `db.py` | SQLite: тіл + тәуліктік лимит |
| `i18n.py` | KZ/RU мәтіндер |
| `config.py` | env баптаулары |
