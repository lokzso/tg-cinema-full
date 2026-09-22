# Telegram Cinema Full

Готовая база Telegram-кинотеатра: бот открывает Telegram Mini App, а Mini App даёт поиск, каталог, сезоны/серии, выбор источника/озвучки/качества, HLS-проигрыватель, избранное и продолжение просмотра.

## Уже реализовано
- Telegram `/start` + кнопка открытия Mini App
- каталог и быстрый поиск
- карточки тайтлов
- сезоны и серии
- подключаемые источники через `app/sources/`
- выбор источника / озвучки / качества
- HLS-плеер через hls.js
- сохранение позиции просмотра каждые 15 секунд
- продолжение просмотра с сохранённого места
- история в разделе «Продолжить»
- избранное
- SQLite без отдельного сервера БД
- healthcheck `/health`
- Docker / docker-compose

## Источники
В сборке установлен публичный тестовый HLS только для демонстрации плеера. Подключайте API, CDN, собственные файлы или HLS/DASH-потоки, на которые у вас есть право доступа и показа. Архитектура источников модульная: новый сервис добавляется отдельным адаптером.

## Быстрый запуск
1. Установить Python 3.12+
2. `python -m venv .venv`
3. Windows: `.venv\\Scripts\\activate`
4. `pip install -r requirements.txt`
5. Скопировать `.env.example` в `.env`
6. Заполнить `BOT_TOKEN`
7. Запустить Web API: `python run_web.py`
8. Запустить бота во втором окне: `python run_bot.py`

## Telegram Mini App и HTTPS
Telegram требует HTTPS для URL Mini App. На хостинге укажите публичный HTTPS-адрес в `WEBAPP_URL`. Для локального теста можно использовать HTTPS-туннель.

## Деплой через Docker
`docker compose up --build`

Для постоянной работы можно держать `web` и `bot` как два процесса/сервиса одного проекта.

## Как добавить разрешённый источник
Создайте файл в `app/sources/`, реализуйте `get_streams(title_id, season, episode)` и верните список `StreamVariant`. Потом зарегистрируйте адаптер в `app/sources/registry.py`.

```python
from .base import StreamVariant

class MySource:
    id = "mysource"
    name = "My CDN"

    async def get_streams(self, title_id, season, episode):
        return [
            StreamVariant(
                source_id=self.id,
                source_name=self.name,
                voice_id="ru1",
                voice_name="Русская дорожка",
                quality="1080p",
                url="https://example.com/master.m3u8",
            )
        ]
```

## Каталог
Демо-каталог лежит в `app/data/catalog.json`. Можно добавлять фильмы/сериалы/аниме вручную либо позже подключить разрешённый API метаданных.

## Структура
- `app/bot.py` — Telegram-бот
- `app/api.py` — FastAPI + API для Mini App
- `app/db.py` — SQLite, прогресс и избранное
- `app/sources/` — адаптеры видеоисточников
- `app/templates/index.html` — Mini App
- `app/static/` — интерфейс + плеер
- `app/data/catalog.json` — каталог

## Что можно добавить дальше
- проверку подписи Telegram `initData` для публичного многопользовательского запуска
- админ-панель для каталога
- метаданные через разрешённый API
- WebVTT-субтитры
- автоматический переход на следующую серию
- кнопки пропуска интро/эндинга
- отдельную историю просмотра
- рейтинг/оценки пользователя
- серверное хранение постеров
