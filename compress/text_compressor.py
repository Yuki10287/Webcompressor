import struct
from compress.huffman import HuffmanCodec
from compress.lz77 import LZ77Codec
from compress.text_preprocessors import TextPreprocessorManager


class TextCompressor:
    strategy_name = "pre_lz77_huffman_text"
    MAGIC = b"TLH1"

    def __init__(self):
        self.huffman_codec = HuffmanCodec()
        self.lz77_codec = LZ77Codec(
            window_size=8192,
            lookahead_size=127,
            min_match=4
        )
        self.preprocessor_manager = TextPreprocessorManager()

    def compress(self, data: bytes, file_path: str = "") -> bytes:
        # 1. 按文件类型做网页特征预处理
        type_id, processed = self.preprocessor_manager.preprocess_by_path(file_path, data)

        # 2. 先做 LZ77，利用重复片段
        lz77_blob = self.lz77_codec.compress(processed)

        # 3. 再做 Huffman，利用符号频率
        payload = struct.pack(">4sB", self.MAGIC, type_id) + lz77_blob
        return self.huffman_codec.compress(payload)

    def decompress(self, data: bytes) -> bytes:
        # 1. 先 Huffman 解码
        decoded = self.huffman_codec.decompress(data)

        if len(decoded) < 5:
            raise ValueError("文本解压失败：头部长度不足")

        magic, type_id = struct.unpack(">4sB", decoded[:5])
        if magic != self.MAGIC:
            raise ValueError("文本解压失败：头部不匹配")

        lz77_blob = decoded[5:]

        # 2. 再 LZ77 解码
        processed = self.lz77_codec.decompress(lz77_blob)

        # 3. 最后逆预处理，恢复原始文本
        return self.preprocessor_manager.restore_by_type(type_id, processed)