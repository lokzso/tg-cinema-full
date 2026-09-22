import json
from pathlib import Path

PATH = Path(__file__).parent / "data" / "catalog.json"

def load_catalog():
    return json.loads(PATH.read_text(encoding="utf-8"))

def get_title(title_id: str):
    for item in load_catalog():
        if item["id"] == title_id:
            return item
    return None

def search_titles(q: str):
    q = q.strip().lower()
    if not q:
        return load_catalog()
    return [x for x in load_catalog() if q in x["title"].lower() or q in x.get("original_title", "").lower()]
