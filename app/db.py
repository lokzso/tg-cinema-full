import sqlite3
from datetime import datetime
from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY,
  username TEXT,
  first_name TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS progress(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  title_id TEXT NOT NULL,
  season INTEGER NOT NULL,
  episode INTEGER NOT NULL,
  position REAL NOT NULL DEFAULT 0,
  duration REAL NOT NULL DEFAULT 0,
  source_id TEXT,
  voice_id TEXT,
  quality TEXT,
  updated_at TEXT NOT NULL,
  UNIQUE(user_id,title_id,season,episode)
);
CREATE TABLE IF NOT EXISTS favorites(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  title_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(user_id,title_id)
);
"""

def conn():
    c = sqlite3.connect(settings.database_path)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with conn() as c:
        c.executescript(SCHEMA)

def upsert_user(user_id:int, username:str|None, first_name:str|None):
    now=datetime.utcnow().isoformat()
    with conn() as c:
        c.execute("""INSERT INTO users(id,username,first_name,created_at) VALUES(?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET username=excluded.username,first_name=excluded.first_name""",
        (user_id,username,first_name,now))

def save_progress(p:dict):
    now=datetime.utcnow().isoformat()
    with conn() as c:
        c.execute("""INSERT INTO progress(user_id,title_id,season,episode,position,duration,source_id,voice_id,quality,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(user_id,title_id,season,episode) DO UPDATE SET
        position=excluded.position,duration=excluded.duration,source_id=excluded.source_id,
        voice_id=excluded.voice_id,quality=excluded.quality,updated_at=excluded.updated_at""",
        (p['user_id'],p['title_id'],p['season'],p['episode'],p['position'],p['duration'],p.get('source_id'),p.get('voice_id'),p.get('quality'),now))

def get_progress(user_id:int,title_id:str,season:int,episode:int):
    with conn() as c:
        return c.execute("SELECT * FROM progress WHERE user_id=? AND title_id=? AND season=? AND episode=?",
                         (user_id,title_id,season,episode)).fetchone()

def get_continue(user_id:int,limit:int=20):
    with conn() as c:
        return c.execute("SELECT * FROM progress WHERE user_id=? ORDER BY updated_at DESC LIMIT ?",(user_id,limit)).fetchall()

def toggle_favorite(user_id:int,title_id:str):
    with conn() as c:
        row=c.execute("SELECT id FROM favorites WHERE user_id=? AND title_id=?",(user_id,title_id)).fetchone()
        if row:
            c.execute("DELETE FROM favorites WHERE id=?",(row['id'],)); return False
        c.execute("INSERT INTO favorites(user_id,title_id,created_at) VALUES(?,?,?)",(user_id,title_id,datetime.utcnow().isoformat())); return True

def favorite_ids(user_id:int):
    with conn() as c:
        return [r['title_id'] for r in c.execute("SELECT title_id FROM favorites WHERE user_id=? ORDER BY created_at DESC",(user_id,)).fetchall()]
