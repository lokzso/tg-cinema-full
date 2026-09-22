from __future__ import annotations

from typing import Protocol


class CatalogProvider(Protocol):
    id: str
    name: str

    async def search(self, query: str, limit: int = 20) -> list[dict]: ...
    async def get_title(self, external_id: str) -> dict | None: ...
