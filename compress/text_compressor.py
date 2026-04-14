import zlib


class TextCompressor:
    strategy_name = "zlib_text"

    def compress(self, data: bytes) -> bytes:
        return zlib.compress(data)

    def decompress(self, data: bytes) -> bytes:
        return zlib.decompress(data)