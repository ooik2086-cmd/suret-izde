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

### Тексеру

Claude Code ішінде:
```
/mcp
```
`veo` тізімде шықса — қосылды.

### Veo мүмкіндіктері

- Мәтін → видео генерациясы
- Сурет → видео (image-to-video)
- Видеоны ұзарту
- Кейіпкер тұрақтылығы (бірнеше сілтеме сурет арқылы)

## Маңызды ескертпелер

- `GOOGLE_API_KEY` — `.env` файлына сақтаңыз (`.gitignore`-да қолданылатын), репоға итермеңіз.
- Veo API — ақылы (секундпен есептеледі). Жаңа Google Cloud аккаунттарына $300 тегін кредит.
- `REPLICATE_API_TOKEN` жоқ болса бот сурет генерациясын тегін (Pollinations) жасайды.
