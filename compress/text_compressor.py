import struct
from compress.huffman import HuffmanCodec
from compress.text_preprocessors import TextPreprocessorManager


class TextCompressor:
    strategy_name = "pre_huffman_text"
    MAGIC = b"TPH1"

    def __init__(self):
        self.codec = HuffmanCodec()
        self.preprocessor_manager = TextPreprocessorManager()

    def compress(self, data: bytes, file_path: str = "") -> bytes:
        type_id, processed = self.preprocessor_manager.preprocess_by_path(file_path, data)

        # 在 Huffman 前加一个很小的头：
        # MAGIC(4字节) + type_id(1字节)
        payload = struct.pack(">4sB", self.MAGIC, type_id) + processed
        return self.codec.compress(payload)

    def decompress(self, data: bytes) -> bytes:
        decoded = self.codec.decompress(data)

        if len(decoded) < 5:
            raise ValueError("文本解压失败：预处理头长度不足")

        magic, type_id = struct.unpack(">4sB", decoded[:5])
        if magic != self.MAGIC:
            raise ValueError("文本解压失败：预处理头不匹配")

        processed = decoded[5:]
        restored = self.preprocessor_manager.restore_by_type(type_id, processed)
        return restored