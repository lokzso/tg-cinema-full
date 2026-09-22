from __future__ import annotations

import httpx

from .base import StreamVariant
from ..config import settings


class AuthorizedJsonSource:
    """
    Optional adapter for an authorized resolver/API you control or are allowed to use.

    Request JSON:
      {title, original_title, year, provider, external_id, season, episode}

    Expected response:
      {"streams": [{"voice_id":"ru","voice_name":"RU","quality":"1080p","url":"https://...m3u8","kind":"hls"}]}
    """

    id = "source_api"

    @property
    def name(self):
        return settings.source_api_name or "Source API"

    async def get_streams(self, title: dict, season: int, episode: int):
        if not settings.source_api_url:
            return []
        headers = {"accept": "application/json", "content-type": "application/json"}
        if settings.source_api_token:
            headers["authorization"] = f"Bearer {settings.source_api_token}"
        payload = {
            "title": title.get("title"), "original_title": title.get("original_title"),
            "year": title.get("year"), "provider": title.get("provider"), "external_id": title.get("external_id"),
            "season": season, "episode": episode,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(settings.source_api_url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
        out = []
        for s in data.get("streams", []):
            if not s.get("url"):
                continue
            out.append(StreamVariant(
                source_id=s.get("source_id") or self.id,
                source_name=s.get("source_name") or self.name,
                voice_id=s.get("voice_id") or "default",
                voice_name=s.get("voice_name") or "По умолчанию",
                quality=s.get("quality") or "Auto",
                url=s["url"], kind=s.get("kind") or "hls",
            ))
        return out
