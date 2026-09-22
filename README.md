# Tg Cinema Full v2

Telegram Mini App + бот с динамическим поиском каталога, агрегатором источников, выбором озвучки/качества, HLS-плеером, избранным и продолжением просмотра.

## Что изменилось в v2
- поиск каталога больше не ограничен `catalog.json`;
- AniList подключён без API-ключа для поиска аниме;
- опционально TMDB для фильмов/сериалов/аниме (`TMDB_BEARER_TOKEN`);
- источники видео собираются параллельно через `app/sources/`;
- выбор `Источник → Озвучка → Качество` раздельный;
- лучший вариант выбирается автоматически, сохранённый вариант восстанавливается;
- PostgreSQL через `DATABASE_URL`, SQLite остаётся fallback для локальной разработки;
- Telegram-бот работает webhook-ом внутри того же FastAPI/Render Web Service;
- `/health` показывает тип БД и режим Telegram.

## Важное разделение
`app/providers/` — только каталог/метаданные (название, постер, сезоны, серии).
`app/sources/` — источники видеопотока. Подключайте только API/CDN/HLS, которые вам разрешено использовать.

То есть поиск может найти `Tokyo Ghoul` через каталог, а после выбора серии `collect_streams()` спрашивает каждый подключённый source-адаптер и собирает варианты в один список.

## Render
Для Render Web Service Docker Command оставьте пустым: используется CMD из Dockerfile.

Environment:
- `BOT_TOKEN` — BotFather token
- `WEBAPP_URL` — публичный URL Render, например `https://tg-cinema-full.onrender.com`
- `DATABASE_URL` — Internal Database URL вашего Render PostgreSQL
- `TELEGRAM_WEBHOOK_SECRET` — случайная строка только из `A-Z a-z 0-9 _ -`
- `WEBHOOK_ENABLED=true`
- `ANILIST_ENABLED=true`
- `TMDB_BEARER_TOKEN` — необязательно, но рекомендуется для полноценного поиска фильмов/сериалов

Health Check Path: `/health`

## Подключение источника без изменения UI
Есть готовый `AuthorizedJsonSource`. Укажите:
- `SOURCE_API_URL=https://your-resolver.example/resolve`
- `SOURCE_API_NAME=My CDN`
- `SOURCE_API_TOKEN=...` (если нужен)

Tg Cinema отправит POST:
```json
{
  "title":"Tokyo Ghoul",
  "original_title":"Tokyo Ghoul",
  "year":2014,
  "provider":"anilist",
  "external_id":"20605",
  "season":1,
  "episode":3
}
```

Ответ API:
```json
{
  "streams":[
    {
      "source_id":"mycdn",
      "source_name":"My CDN",
      "voice_id":"ru_dub",
      "voice_name":"Русская озвучка",
      "quality":"1080p",
      "url":"https://cdn.example/video/master.m3u8",
      "kind":"hls"
    }
  ]
}
```

Можно добавить сколько угодно отдельных Python-адаптеров в `app/sources/registry.py`.

## Локальный запуск
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.api:app --reload
```

Для локального polling вместо webhook:
```env
WEBHOOK_ENABLED=false
```
и во втором терминале:
```bash
python run_bot.py
```
