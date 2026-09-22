from .demo import DemoSource

SOURCES = [DemoSource()]

async def collect_streams(title_id: str, season: int, episode: int):
    result = []
    for src in SOURCES:
        try:
            result.extend(await src.get_streams(title_id, season, episode))
        except Exception:
            continue
    return result
