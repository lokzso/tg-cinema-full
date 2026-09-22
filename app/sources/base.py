from dataclasses import dataclass
from typing import Protocol

@dataclass
class StreamVariant:
    source_id: str
    source_name: str
    voice_id: str
    voice_name: str
    quality: str
    url: str
    kind: str = "hls"

class SourceAdapter(Protocol):
    id: str
    name: str
    async def get_streams(self, title_id: str, season: int, episode: int) -> list[StreamVariant]: ...
