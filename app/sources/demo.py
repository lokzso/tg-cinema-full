from .base import StreamVariant

class DemoSource:
    id = "demo"
    name = "Demo HLS"

    async def get_streams(self, title_id: str, season: int, episode: int):
        # Public test HLS streams. Replace with authorized/legal stream URLs.
        return [
            StreamVariant(self.id, self.name, "original", "Оригинал", "Auto", "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"),
            StreamVariant(self.id, self.name, "alt", "Альтернативная", "Auto", "https://test-streams.mux.dev/test_001/stream.m3u8"),
        ]
