from __future__ import annotations

from ..catalog import load_catalog


class LocalCatalogProvider:
    id = "local"
    name = "Local"

    async def search(self, query: str, limit: int = 20) -> list[dict]:
        q = query.strip().lower()
        items = load_catalog()
        if q:
            items = [x for x in items if q in x.get("title", "").lower() or q in x.get("original_title", "").lower()]
        return [self._wrap(x) for x in items[:limit]]

    async def get_title(self, external_id: str) -> dict | None:
        for x in load_catalog():
            if x["id"] == external_id:
                return self._wrap(x)
        return None

    def _wrap(self, item: dict) -> dict:
        x = dict(item)
        x["id"] = f"{self.id}:{item['id']}"
        x["provider"] = self.id
        x["provider_name"] = self.name
        x["external_id"] = item["id"]
        return x
