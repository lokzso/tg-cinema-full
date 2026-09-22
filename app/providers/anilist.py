from __future__ import annotations

import html
import re
import httpx

from ..config import settings

API = "https://graphql.anilist.co"

SEARCH_QUERY = """
query ($search: String, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(search: $search, type: ANIME, sort: [POPULARITY_DESC]) {
      id title { romaji english native } coverImage { extraLarge large }
      seasonYear startDate { year } genres episodes format description
    }
  }
}
"""

TRENDING_QUERY = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(type: ANIME, sort: [TRENDING_DESC, POPULARITY_DESC]) {
      id title { romaji english native } coverImage { extraLarge large }
      seasonYear startDate { year } genres episodes format description
    }
  }
}
"""

DETAIL_QUERY = """
query ($id: Int) {
  Media(id: $id, type: ANIME) {
    id title { romaji english native } coverImage { extraLarge large }
    seasonYear startDate { year } genres episodes format description
  }
}
"""


def _clean_html(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


class AniListProvider:
    id = "anilist"
    name = "AniList"

    async def _query(self, query: str, variables: dict) -> dict:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.post(API, json={"query": query, "variables": variables})
            r.raise_for_status()
            return r.json()["data"]

    async def search(self, query: str, limit: int = 20) -> list[dict]:
        if not settings.anilist_enabled:
            return []
        if query.strip():
            data = await self._query(SEARCH_QUERY, {"search": query.strip(), "page": 1, "perPage": min(limit, 30)})
        else:
            data = await self._query(TRENDING_QUERY, {"page": 1, "perPage": min(limit, 30)})
        return [self._normalize(x) for x in data["Page"]["media"]]

    async def get_title(self, external_id: str) -> dict | None:
        if not settings.anilist_enabled or not external_id.isdigit():
            return None
        data = await self._query(DETAIL_QUERY, {"id": int(external_id)})
        media = data.get("Media")
        return self._normalize(media, details=True) if media else None

    def _normalize(self, x: dict, details: bool = False) -> dict:
        titles = x.get("title") or {}
        title = titles.get("english") or titles.get("romaji") or titles.get("native") or f"Anime {x['id']}"
        original = titles.get("romaji") or titles.get("native") or title
        year = x.get("seasonYear") or (x.get("startDate") or {}).get("year")
        episodes_count = int(x.get("episodes") or 1)
        episodes_count = max(1, min(episodes_count, 500))
        item = {
            "id": f"{self.id}:{x['id']}",
            "provider": self.id,
            "provider_name": self.name,
            "external_id": str(x["id"]),
            "title": title,
            "original_title": original,
            "year": year or "—",
            "type": "anime",
            "poster": (x.get("coverImage") or {}).get("extraLarge") or (x.get("coverImage") or {}).get("large") or "",
            "description": _clean_html(x.get("description")),
            "genres": x.get("genres") or [],
        }
        if details:
            item["seasons"] = [{
                "number": 1,
                "episodes": [{"number": n, "title": f"Серия {n}", "duration": 0} for n in range(1, episodes_count + 1)]
            }]
        return item
