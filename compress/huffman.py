import heapq
import struct
from collections import Counter
from typing import Dict, Optional


class HuffmanNode:
    __slots__ = ("freq", "byte", "left", "right")

    def __init__(
        self,
        freq: int,
        byte: Optional[int] = None,
        left: Optional["HuffmanNode"] = None,
        right: Optional["HuffmanNode"] = None
    ):
        self.freq = freq
        self.byte = byte
        self.left = left
        self.right = right

    def __lt__(self, other: "HuffmanNode") -> bool:
        return self.freq < other.freq

    @property
    def is_leaf(self) -> bool:
        return self.byte is not None


class HuffmanCodec:
    MAGIC = b"HUF1"

    def compress(self, data: bytes) -> bytes:
        if not data:
            # magic + original_length + unique_count
            return struct.pack(">4sIH", self.MAGIC, 0, 0)

        freq_map = Counter(data)
        root = self._build_tree(freq_map)
        code_map = self._build_code_map(root)

        header = bytearray()
        header.extend(struct.pack(">4sIH", self.MAGIC, len(data), len(freq_map)))

        for byte_value, freq in freq_map.items():
            header.extend(struct.pack(">BI", byte_value, freq))

        payload = self._encode_payload(data, code_map)
        return bytes(header) + payload

    def decompress(self, blob: bytes) -> bytes:
        if len(blob) < 10:
            raise ValueError("无效的 Huffman 压缩数据：长度过短")

        magic, original_length, unique_count = struct.unpack(">4sIH", blob[:10])
        if magic != self.MAGIC:
            raise ValueError("无效的 Huffman 压缩数据：文件头不匹配")

        offset = 10
        freq_map: Dict[int, int] = {}

        for _ in range(unique_count):
            if offset + 5 > len(blob):
                raise ValueError("无效的 Huffman 压缩数据：频率表损坏")
            byte_value, freq = struct.unpack(">BI", blob[offset:offset + 5])
            freq_map[byte_value] = freq
            offset += 5

        if original_length == 0:
            return b""

        root = self._build_tree(freq_map)
        payload = blob[offset:]

        # 只有一种字符时，压缩体可能为空，直接恢复
        if root.is_leaf:
            return bytes([root.byte]) * original_length

        result = bytearray()
        node = root

        for byte_value in payload:
            for bit_index in range(7, -1, -1):
                bit = (byte_value >> bit_index) & 1
                node = node.left if bit == 0 else node.right

                if node.is_leaf:
                    result.append(node.byte)
                    if len(result) == original_length:
                        return bytes(result)
                    node = root

        if len(result) != original_length:
            raise ValueError("Huffman 解压失败：恢复长度不正确")

        return bytes(result)

    def _build_tree(self, freq_map: Dict[int, int]) -> HuffmanNode:
        heap = [HuffmanNode(freq=freq, byte=byte_value) for byte_value, freq in freq_map.items()]
        heapq.heapify(heap)

        if len(heap) == 1:
            return heap[0]

        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            parent = HuffmanNode(freq=left.freq + right.freq, left=left, right=right)
            heapq.heappush(heap, parent)

        return heap[0]

    def _build_code_map(self, root: HuffmanNode) -> Dict[int, str]:
        code_map: Dict[int, str] = {}

        def dfs(node: HuffmanNode, path: str) -> None:
            if node.is_leaf:
                # 单一字符时也必须给一个编码
                code_map[node.byte] = path if path else "0"
                return
            dfs(node.left, path + "0")
            dfs(node.right, path + "1")

        dfs(root, "")
        return code_map

    def _encode_payload(self, data: bytes, code_map: Dict[int, str]) -> bytes:
        output = bytearray()
        current_byte = 0
        bit_count = 0

        for b in data:
            code = code_map[b]
            for ch in code:
                current_byte = (current_byte << 1) | (1 if ch == "1" else 0)
                bit_count += 1

                if bit_count == 8:
                    output.append(current_byte)
                    current_byte = 0
                    bit_count = 0

        if bit_count > 0:
            current_byte <<= (8 - bit_count)
            output.append(current_byte)

        return bytes(output)