from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .db import init_db, upsert_user, save_progress as db_save_progress, get_progress as db_get_progress, get_continue, toggle_favorite, favorite_ids
from .catalog import load_catalog, get_title, search_titles
from .sources.registry import collect_streams

app = FastAPI(title="Telegram Cinema")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/catalog")
def catalog(q: str = ""):
    return search_titles(q)

@app.get("/api/title/{title_id}")
def title(title_id: str):
    item = get_title(title_id)
    if not item:
        raise HTTPException(404)
    return item

@app.get("/api/streams/{title_id}/{season}/{episode}")
async def streams(title_id: str, season: int, episode: int):
    variants = await collect_streams(title_id, season, episode)
    return [v.__dict__ for v in variants]

class UserPayload(BaseModel):
    user_id: int
    username: str | None = None
    first_name: str | None = None

@app.post("/api/user")
def user_endpoint(p: UserPayload):
    upsert_user(p.user_id,p.username,p.first_name)
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

@app.get("/api/progress/{user_id}/{title_id}/{season}/{episode}")
def progress_get(user_id: int, title_id: str, season: int, episode: int):
    row=db_get_progress(user_id,title_id,season,episode)
    if not row: return None
    return {"position":row['position'],"duration":row['duration'],"source_id":row['source_id'],"voice_id":row['voice_id'],"quality":row['quality']}

@app.get("/api/continue/{user_id}")
def continue_watching(user_id: int):
    out=[]
    for r in get_continue(user_id):
        t=get_title(r['title_id'])
        if t:
            out.append({"title":t,"season":r['season'],"episode":r['episode'],"position":r['position'],"duration":r['duration']})
    return out

class FavPayload(BaseModel):
    user_id: int
    title_id: str

@app.post("/api/favorite/toggle")
def fav_toggle(p: FavPayload):
    return {"favorite":toggle_favorite(p.user_id,p.title_id)}

@app.get("/api/favorites/{user_id}")
def favorites(user_id:int):
    ids=set(favorite_ids(user_id))
    return [t for t in load_catalog() if t['id'] in ids]
