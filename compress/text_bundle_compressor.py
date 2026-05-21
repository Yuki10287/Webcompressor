import struct
from typing import Dict, List, Tuple

from compress.huffman import HuffmanCodec
from compress.lz77 import LZ77Codec
from compress.text_preprocessors import TextPreprocessorManager


class TextBundleCompressor:
    """
    整站文本资源压缩器。

    多个 HTML/CSS/JS/JSON 等文本文件先被打成一个 bundle，再整体做 LZ77 和 Huffman。
    这样可以利用不同页面、样式和脚本之间的重复片段，比逐文件压缩更容易获得收益。

    bundle 原始格式：
    TBD1(4字节) + 文件数量(2字节)
    + 若干个 entry：
      ENT1(4字节) + 文本类型(1字节) + 路径长度(2字节) + 预处理后数据长度(4字节)
      + UTF-8 相对路径 + 预处理后文件内容
    """

    MAGIC = b"TBD1"
    ENTRY_MAGIC = b"ENT1"
    strategy_name = "bundle_pre_lz77_huffman_text"

    def __init__(self):
        self.preprocessor_manager = TextPreprocessorManager()
        self.lz77_codec = LZ77Codec(
            window_size=8192,
            lookahead_size=127,
            min_match=4
        )
        self.huffman_codec = HuffmanCodec()

    def compress_files(self, files: List[Tuple[str, bytes]]) -> bytes:
        """
        files: [(relative_path, raw_bytes), ...]
        返回整个文本 bundle 的最终压缩结果。
        """
        bundle = bytearray()
        bundle.extend(struct.pack(">4sH", self.MAGIC, len(files)))

        for relative_path, raw_data in files:
            normalized_path = relative_path.replace("\\", "/")
            path_bytes = normalized_path.encode("utf-8")

            type_id, processed = self.preprocessor_manager.preprocess_by_path(
                normalized_path, raw_data
            )

            # entry 头部保存路径和数据长度，解压时才能按原目录结构拆回多个文件。
            bundle.extend(struct.pack(">4sBHI", self.ENTRY_MAGIC, type_id, len(path_bytes), len(processed)))
            bundle.extend(path_bytes)
            bundle.extend(processed)

        # 先用 LZ77 捕捉长距离重复片段，再用 Huffman 压缩 LZ77 token 的字节分布。
        lz77_blob = self.lz77_codec.compress(bytes(bundle))
        final_blob = self.huffman_codec.compress(lz77_blob)
        return final_blob

    def decompress_files(self, blob: bytes) -> Dict[str, bytes]:
        """
        返回：
        {
            "index.html": b"...",
            "css/base.css": b"...",
            ...
        }
        """
        # 解压顺序必须和压缩顺序相反：Huffman -> LZ77 -> bundle 拆包 -> 逆预处理。
        lz77_blob = self.huffman_codec.decompress(blob)
        bundle = self.lz77_codec.decompress(lz77_blob)

        if len(bundle) < 6:
            raise ValueError("无效的 bundle 数据：长度不足")

        magic, file_count = struct.unpack(">4sH", bundle[:6])
        if magic != self.MAGIC:
            raise ValueError("无效的 bundle 数据：文件头不匹配")

        offset = 6
        restored: Dict[str, bytes] = {}

        for _ in range(file_count):
            if offset + 11 > len(bundle):
                raise ValueError("无效的 bundle 数据：entry 头部不足")

            entry_magic, type_id, path_len, data_len = struct.unpack(
                ">4sBHI", bundle[offset:offset + 11]
            )
            offset += 11

            if entry_magic != self.ENTRY_MAGIC:
                raise ValueError("无效的 bundle 数据：entry magic 不匹配")

            if offset + path_len > len(bundle):
                raise ValueError("无效的 bundle 数据：路径数据不足")
            path_bytes = bundle[offset:offset + path_len]
            offset += path_len

            if offset + data_len > len(bundle):
                raise ValueError("无效的 bundle 数据：文本数据不足")
            processed = bundle[offset:offset + data_len]
            offset += data_len

            relative_path = path_bytes.decode("utf-8")
            raw_data = self.preprocessor_manager.restore_by_type(type_id, processed)
            restored[relative_path] = raw_data

        return restored
