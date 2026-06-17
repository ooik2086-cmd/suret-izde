# suret-izde — Claude Code нұсқаулығы

Қазақша/орысша интерфейсі бар Telegram AI-бот (сурет + видео генерациясы).

## Жоба структурасы

| Файл | Мақсаты |
|---|---|
| `aibot/bot.py` | aiogram хендлерлері, Stars төлемі, health сервер |
| `aibot/providers.py` | FreeProvider (Pollinations), ReplicateProvider, HybridProvider |
| `aibot/config.py` | Барлық env баптаулары |
| `aibot/db.py` | SQLite: тіл, тәуліктік лимит, кредиттер |
| `aibot/i18n.py` | KZ/RU аудармалар |

## Жергілікті іске қосу

```bash
cd aibot
pip install -r requirements.txt
export BOT_TOKEN=<telegram_bot_token>
python bot.py
```

## Сынақтар

```bash
python -m pytest -q
```

## MCP серверлері

### Veo (Google видео генерациясы)

Конфигурация `.mcp.json`-да. Іске қосу алдында `GOOGLE_API_KEY` орнатыңыз:

```bash
# Linux / macOS / WSL
export GOOGLE_API_KEY=ваш_google_api_key

# Windows PowerShell
$env:GOOGLE_API_KEY = "ваш_google_api_key"

# Windows CMD
set GOOGLE_API_KEY=ваш_google_api_key
```

API кілтін алу: [aistudio.google.com](https://aistudio.google.com) → "Get API key".

**Windows-та npx жұмыс істемесе**, `.mcp.json`-ды өзгертіңіз:

```json
{
  "mcpServers": {
    "veo": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "google-veo3-1-mcp-server"]
    }
  }
}
```

### Imagen (Google сурет генерациясы)

`gemini-imagen4` пакеті — Imagen 4.0 модельдері (Standard, Fast, Ultra). `GEMINI_API_KEY` қажет — бұл да [aistudio.google.com](https://aistudio.google.com)-дан алынатын сол кілт (`GOOGLE_API_KEY`-мен бірдей мән):

```bash
# Linux / macOS / WSL
export GEMINI_API_KEY=ваш_google_api_key

# Windows PowerShell
$env:GEMINI_API_KEY = "ваш_google_api_key"

# Windows CMD
set GEMINI_API_KEY=ваш_google_api_key
```

**Imagen мүмкіндіктері:**
- Мәтін → сурет (Imagen 4 Standard/Fast/Ultra)
- Ен/биіктік қатынасы: 1:1, 3:4, 4:3, 9:16, 16:9
- PNG / JPEG шығысы
- Суреттер жергілікті файлға сақталады

**Windows-та npx жұмыс істемесе** (`imagen` серверін де `cmd /c` арқылы іске қосыңыз):

```json
{
  "mcpServers": {
    "veo": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "google-veo3-1-mcp-server"]
    },
    "imagen": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "gemini-imagen4"]
    }
  }
}
```

### Тексеру

Claude Code ішінде:
```
/mcp
```
`veo` және `imagen` екеуі де тізімде шықса — дайын.

### Veo мүмкіндіктері

- Мәтін → видео генерациясы
- Сурет → видео (image-to-video)
- Видеоны ұзарту
- Кейіпкер тұрақтылығы (бірнеше сілтеме сурет арқылы)

## Маңызды ескертпелер

- `GOOGLE_API_KEY` / `GEMINI_API_KEY` — [aistudio.google.com](https://aistudio.google.com)-дан алынады, **бірдей кілт**.
- Екеуін де `.env` файлына сақтаңыз (`.gitignore`-да бар), репоға итермеңіз.
- Veo API — ақылы (секундпен есептеледі). Imagen да ақылы. Жаңа Google Cloud аккаунттарына $300 тегін кредит.
- `REPLICATE_API_TOKEN` жоқ болса бот сурет генерациясын тегін (Pollinations) жасайды.
