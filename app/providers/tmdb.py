from __future__ import annotations

import asyncio
import httpx

from ..config import settings

BASE = "https://api.themoviedb.org/3"
IMG = "https://image.tmdb.org/t/p/w780"


class TMDBProvider:
    id = "tmdb"
    name = "TMDB"

    def _headers(self):
        return {"Authorization": f"Bearer {settings.tmdb_bearer_token}", "accept": "application/json"}

    async def search(self, query: str, limit: int = 20) -> list[dict]:
        if not settings.tmdb_bearer_token or not query.strip():
            return []
        async with httpx.AsyncClient(timeout=12, headers=self._headers()) as client:
            r = await client.get(f"{BASE}/search/multi", params={"query": query, "language": "ru-RU", "include_adult": "false"})
            r.raise_for_status()
            items = []
            for x in r.json().get("results", []):
                if x.get("media_type") not in {"movie", "tv"}:
                    continue
                items.append(self._normalize_search(x))
                if len(items) >= limit:
                    break
            return items

    async def get_title(self, external_id: str) -> dict | None:
        if not settings.tmdb_bearer_token:
            return None
        try:
            media_type, raw_id = external_id.split("-", 1)
            item_id = int(raw_id)
        except Exception:
            return None
        if media_type not in {"movie", "tv"}:
            return None

        async with httpx.AsyncClient(timeout=15, headers=self._headers()) as client:
            r = await client.get(f"{BASE}/{media_type}/{item_id}", params={"language": "ru-RU"})
            if r.status_code == 404:
                return None
            r.raise_for_status()
            x = r.json()
            if media_type == "movie":
                return self._normalize_movie_detail(x)

            seasons_meta = [s for s in x.get("seasons", []) if int(s.get("season_number", 0)) > 0]
            season_tasks = [client.get(f"{BASE}/tv/{item_id}/season/{s['season_number']}", params={"language": "ru-RU"}) for s in seasons_meta]
            responses = await asyncio.gather(*season_tasks, return_exceptions=True)
            seasons = []
            for sm, resp in zip(seasons_meta, responses):
                eps = []
                if not isinstance(resp, Exception) and resp.status_code == 200:
                    for e in resp.json().get("episodes", []):
                        eps.append({"number": e.get("episode_number", 1), "title": e.get("name") or f"Серия {e.get('episode_number', 1)}", "duration": int(e.get("runtime") or 0) * 60})
                if not eps:
                    eps = [{"number": n, "title": f"Серия {n}", "duration": 0} for n in range(1, int(sm.get("episode_count") or 1) + 1)]
                seasons.append({"number": sm["season_number"], "episodes": eps})
            return {
                "id": f"tmdb:tv-{item_id}", "provider": self.id, "provider_name": self.name,
                "external_id": f"tv-{item_id}", "title": x.get("name") or x.get("original_name") or str(item_id),
                "original_title": x.get("original_name") or x.get("name") or "", "year": (x.get("first_air_date") or "")[:4] or "—",
                "type": "series", "poster": IMG + x["poster_path"] if x.get("poster_path") else "",
                "description": x.get("overview") or "", "genres": [g.get("name") for g in x.get("genres", []) if g.get("name")],
                "seasons": seasons or [{"number": 1, "episodes": [{"number": 1, "title": "Серия 1", "duration": 0}]}],
            }

    def _normalize_search(self, x: dict) -> dict:
        mt = x["media_type"]
        title = x.get("title") if mt == "movie" else x.get("name")
        original = x.get("original_title") if mt == "movie" else x.get("original_name")
        date = x.get("release_date") if mt == "movie" else x.get("first_air_date")
        return {
            "id": f"tmdb:{mt}-{x['id']}", "provider": self.id, "provider_name": self.name,
            "external_id": f"{mt}-{x['id']}", "title": title or original or str(x["id"]),
            "original_title": original or title or "", "year": (date or "")[:4] or "—",
            "type": "movie" if mt == "movie" else "series",
            "poster": IMG + x["poster_path"] if x.get("poster_path") else "", "description": x.get("overview") or "", "genres": [],
        }

    def _normalize_movie_detail(self, x: dict) -> dict:
        item_id = x["id"]
        return {
            "id": f"tmdb:movie-{item_id}", "provider": self.id, "provider_name": self.name,
            "external_id": f"movie-{item_id}", "title": x.get("title") or x.get("original_title") or str(item_id),
            "original_title": x.get("original_title") or x.get("title") or "", "year": (x.get("release_date") or "")[:4] or "—",
            "type": "movie", "poster": IMG + x["poster_path"] if x.get("poster_path") else "",
            "description": x.get("overview") or "", "genres": [g.get("name") for g in x.get("genres", []) if g.get("name")],
            "seasons": [{"number": 1, "episodes": [{"number": 1, "title": "Фильм", "duration": int(x.get("runtime") or 0) * 60}]}],
        }
