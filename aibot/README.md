# 🤖 AI-генератор Telegram бот

Адамдар ботқа жазады → бот AI арқылы **сурет / видео / фото жаңарту / аватар / суретті жандандыру** жасап береді.
Қазір **тегін лимитпен** (тәулігіне әр пайдаланушыға) жұмыс істейді; кейін төлем (Telegram Stars) қосуға дайын.

- 🇰🇿 Қазақша / 🇷🇺 Орысша интерфейс
- 💎 **Telegram Stars төлемі** — лимит біткенде қосымша генерация сатылады (банк қажет емес).
- Бэкенд:
  - **Тегін, кілтсіз** — сурет генерациясы Pollinations арқылы нақты жұмыс істейді (API кілті де, төлем де керек емес).
  - **Replicate** (`REPLICATE_API_TOKEN` қосылса) — видео, фото жаңарту, аватар да қосылады.
- Хостинг: Render тегін web-сервис (long-polling + health сервер қатар).

> ⚠️ Тек **`BOT_TOKEN`** міндетті. Онсыз бот іске қосылмайды (Telegram талабы).
> `REPLICATE_API_TOKEN` болмаса — бот тегін режимде нақты **сурет** жасайды,
> ал видео/жаңарту/аватар үшін кілт қажеттігін сыпайы хабарлайды.

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
сурет тегін, кілтсіз (Pollinations) нақты жасалады; қалған режимдер кілт сұрайды.

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
| `REPLICATE_API_TOKEN` | — | Replicate кілті (жоқ болса: сурет тегін істейді, қалғаны кілт сұрайды) |
| `LIMIT_IMAGE` | 5 | Тәуліктік тегін сурет лимиті |
| `LIMIT_VIDEO` | 1 | Тәуліктік тегін видео лимиті |
| `LIMIT_RESTORE` | 3 | Тәуліктік фото жаңарту лимиті |
| `LIMIT_AVATAR` | 3 | Тәуліктік аватар лимиті |
| `LIMIT_ANIMATE` | 1 | Тәуліктік «суретті жандандыру» лимиті |
| `DISABLE_VIDEO` | — | `1` болса видео мүлдем өшеді (шығынды бақылау) |
| `MODEL_IMAGE` | `black-forest-labs/flux-schnell` | Replicate моделі |
| `MODEL_VIDEO` | `minimax/video-01` | Replicate моделі |
| `MODEL_RESTORE` | `tencentarc/gfpgan` | Replicate моделі |
| `MODEL_AVATAR` | `tencentarc/photomaker` | Replicate моделі |
| `MODEL_ANIMATE` | `fofr/live-portrait` | Сурет+видео → жандандыру моделі |
| `ANIMATE_IMAGE_FIELD` | `face_image` | Animate моделінің сурет өрісінің аты |
| `ANIMATE_VIDEO_FIELD` | `driving_video` | Animate моделінің видео өрісінің аты |
| `DEFAULT_LANG` | `kz` | Әдепкі тіл (`kz`/`ru`) |

### 🎭 «Суретті жандандыру» (animate) туралы

Пайдаланушы **сурет + қозғалыс видеосын** жібереді → бот суреттегі кейіпкерді
видеодағы қозғалыспен жандандырады. Бұл режим **тек Replicate** арқылы жұмыс
істейді (тегін нұсқасы жоқ) және **кілт + аздаған ақы** қажет етеді.

Әдепкі модель — `fofr/live-portrait` (бет/портретке өте жақсы, арзан). Толық
дене қозғалысы керек болса, дашбордта мынаны өзгертіңіз:
- `MODEL_ANIMATE` = мыс. `zsxkib/mimicmotion`
- `ANIMATE_IMAGE_FIELD` / `ANIMATE_VIDEO_FIELD` = сол модельдің кіріс өрістерінің
  аттары (Replicate бетіндегі «Input schema» бойынша).

> Telegram боты файлды **20 МБ-қа дейін** ғана жүктей алады — видео қысқа болсын.
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

## 4. Қалай ақша табады (төлем дайын ✅)

1. **Тегін лимит** — әркім күніне бірнеше тегін генерация жасайды (тарту үшін).
2. **Жазылым (негізгі)** — «💎 Сатып алу» → **Telegram Stars** арқылы:
   - 📅 1 апта — 150⭐ (~$2)
   - 📆 1 ай — 650⭐ (~$10)
   Жазылым кезінде **шексіз** қолдану. `config.SUBSCRIPTIONS`-тен өзгертіңіз.
3. **Кредит (қосымша)** — `config.PACKAGES` арқылы дербес генерация да сатуға болады.
4. **Маржа** — сурет тегін ($0, Pollinations), видео Replicate-ке ақылы. Жазылым
   бағасы шығыннан жоғары болуын қадағалаңыз. Stars-ты Telegram арқылы (TON) ақшаға
   шығарасыз.

> ⚠️ Жазылым **шексіз** болғандықтан, видео шығынын бақылаңыз. Қаласаңыз видеоны
> жазылымнан тыс қалдырып, тек кредитпен сатуға болады.
>
> Төлем коды толық: `aiogram` Telegram Stars (`XTR`), `answer_invoice` +
> `pre_checkout` + `successful_payment`. Жазылым/кредит — `subs`/`credits` кестелерінде.

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
| `bot.py` | aiogram хендлерлері, мәзір, генерация ағыны, Stars төлемі, health сервер |
| `providers.py` | Free (Pollinations) / Replicate / Demo провайдерлері (ауыстырмалы «ми») |
| `db.py` | SQLite: тіл + тәуліктік лимит + төленген кредиттер |
| `i18n.py` | KZ/RU мәтіндер |
| `config.py` | env баптаулары |
