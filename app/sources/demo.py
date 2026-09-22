from .base import StreamVariant


class DemoSource:
    id = "demo"
    name = "Demo HLS"

    async def get_streams(self, title: dict, season: int, episode: int):
        # Demo video is shown only for local demo titles, never for real catalog results.
        if title.get("provider") != "local":
            return []
        return [
            StreamVariant(self.id, self.name, "original", "Оригинал", "1080p", "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"),
            StreamVariant(self.id, self.name, "alt", "Альтернативная", "720p", "https://test-streams.mux.dev/test_001/stream.m3u8"),
        ]
