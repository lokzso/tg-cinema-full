from __future__ import annotations

import asyncio
import re

from .demo import DemoSource
from .http_json import AuthorizedJsonSource

SOURCES = [DemoSource(), AuthorizedJsonSource()]


def _quality_score(q: str) -> int:
    m = re.search(r"(\d{3,4})", q or "")
    if m:
        return int(m.group(1))
    if (q or "").lower() == "auto":
        return 900
    return 0


async def collect_streams(title: dict, season: int, episode: int):
    chunks = await asyncio.gather(
        *(src.get_streams(title, season, episode) for src in SOURCES),
        return_exceptions=True,
    )
    result = []
    seen = set()
    for chunk in chunks:
        if isinstance(chunk, Exception):
            continue
        for v in chunk:
            key = (v.source_id, v.voice_id, v.quality, v.url)
            if key in seen:
                continue
            seen.add(key)
            result.append(v)
    result.sort(key=lambda x: (_quality_score(x.quality), x.source_name, x.voice_name), reverse=True)
    return result
