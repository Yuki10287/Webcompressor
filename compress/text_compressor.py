from compress.huffman import HuffmanCodec


class TextCompressor:
    strategy_name = "huffman_text"

    def __init__(self):
        self.codec = HuffmanCodec()

    def compress(self, data: bytes) -> bytes:
        return self.codec.compress(data)

    def decompress(self, data: bytes) -> bytes:
        return self.codec.decompress(data)