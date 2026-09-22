from __future__ import annotations

import asyncio

from .local import LocalCatalogProvider
from .anilist import AniListProvider
from .tmdb import TMDBProvider

PROVIDERS = [LocalCatalogProvider(), AniListProvider(), TMDBProvider()]
PROVIDER_MAP = {p.id: p for p in PROVIDERS}


async def search_catalog(query: str, limit: int = 30) -> list[dict]:
    calls = [p.search(query, limit=limit) for p in PROVIDERS]
    chunks = await asyncio.gather(*calls, return_exceptions=True)
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for chunk in chunks:
        if isinstance(chunk, Exception):
            continue
        for item in chunk:
            key = (str(item.get("title", "")).strip().casefold(), str(item.get("year", "")))
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
    return out[:limit]


async def get_catalog_title(title_id: str) -> dict | None:
    if ":" not in title_id:
        return None
    provider_id, external_id = title_id.split(":", 1)
    provider = PROVIDER_MAP.get(provider_id)
    if not provider:
        return None
    return await provider.get_title(external_id)
