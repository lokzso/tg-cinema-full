from __future__ import annotations

import asyncio

from aiogram.types import Update
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .config import settings
from .db import (
    init_db, upsert_user, save_progress as db_save_progress, get_progress as db_get_progress,
    get_continue, toggle_favorite, favorite_ids, database_kind,
)
from .providers.registry import search_catalog, get_catalog_title
from .sources.registry import collect_streams
from .bot import bot, dp, setup_webhook, close_bot

app = FastAPI(title="Tg Cinema")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
async def startup():
    init_db()
    await setup_webhook()


@app.on_event("shutdown")
async def shutdown():
    await close_bot()


@app.get("/health")
def health():
    return {"ok": True, "database": database_kind(), "telegram": "webhook" if settings.webhook_enabled else "polling"}


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request, x_telegram_bot_api_secret_token: str | None = Header(default=None)):
    if not bot:
        raise HTTPException(503, "Bot is disabled")
    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(403, "Bad webhook secret")
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/catalog")
async def catalog(q: str = ""):
    return await search_catalog(q, limit=30)


@app.get("/api/title/{title_id:path}")
async def title(title_id: str):
    item = await get_catalog_title(title_id)
    if not item:
        raise HTTPException(404, "Title not found")
    return item


@app.get("/api/streams/{title_id:path}")
async def streams(title_id: str, season: int, episode: int):
    item = await get_catalog_title(title_id)
    if not item:
        raise HTTPException(404, "Title not found")
    variants = await collect_streams(item, season, episode)
    return [v.__dict__ for v in variants]


class UserPayload(BaseModel):
    user_id: int
    username: str | None = None
    first_name: str | None = None


@app.post("/api/user")
def user_endpoint(p: UserPayload):
    upsert_user(p.user_id, p.username, p.first_name)
    return {"ok": True}


class ProgressPayload(BaseModel):
    user_id: int
    title_id: str
    season: int
    episode: int
    position: float = 0
    duration: float = 0
    source_id: str | None = None
    voice_id: str | None = None
    quality: str | None = None


@app.post("/api/progress")
def progress_save(p: ProgressPayload):
    db_save_progress(p.model_dump())
    return {"ok": True}


@app.get("/api/progress/{user_id}/{title_id:path}")
def progress_get(user_id: int, title_id: str, season: int, episode: int):
    row = db_get_progress(user_id, title_id, season, episode)
    if not row:
        return None
    return {
        "position": row["position"], "duration": row["duration"], "source_id": row["source_id"],
        "voice_id": row["voice_id"], "quality": row["quality"],
    }


@app.get("/api/continue/{user_id}")
async def continue_watching(user_id: int):
    rows = get_continue(user_id)
    titles = await asyncio.gather(*(get_catalog_title(r["title_id"]) for r in rows), return_exceptions=True)
    out = []
    for r, t in zip(rows, titles):
        if isinstance(t, Exception) or not t:
            continue
        out.append({"title": t, "season": r["season"], "episode": r["episode"], "position": r["position"], "duration": r["duration"]})
    return out


class FavPayload(BaseModel):
    user_id: int
    title_id: str


@app.post("/api/favorite/toggle")
def fav_toggle(p: FavPayload):
    return {"favorite": toggle_favorite(p.user_id, p.title_id)}


@app.get("/api/favorites/{user_id}")
async def favorites_endpoint(user_id: int):
    ids = favorite_ids(user_id)
    titles = await asyncio.gather(*(get_catalog_title(x) for x in ids), return_exceptions=True)
    return [x for x in titles if x and not isinstance(x, Exception)]
