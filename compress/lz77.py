import struct


class LZ77Codec:
    MAGIC = b"LZ77"

    def __init__(self, window_size: int = 2048, lookahead_size: int = 64, min_match: int = 3):
        self.window_size = window_size
        self.lookahead_size = lookahead_size
        self.min_match = min_match

    def compress(self, data: bytes) -> bytes:
        """
        输出格式：
        MAGIC(4) + original_length(4) + token_stream

        token_stream:
        - 字面量: flag=0 + byte(1)
        - 匹配项: flag=1 + offset(2) + length(2)
        """
        header = struct.pack(">4sI", self.MAGIC, len(data))
        output = bytearray()
        i = 0
        n = len(data)

        while i < n:
            best_offset = 0
            best_length = 0

            window_start = max(0, i - self.window_size)
            max_len = min(self.lookahead_size, n - i)

            # 在滑动窗口中找最长匹配
            for j in range(window_start, i):
                match_len = self._match_length(data, j, i, max_len)

                if match_len > best_length:
                    best_length = match_len
                    best_offset = i - j

            if best_length >= self.min_match:
                output.append(1)
                output.extend(struct.pack(">HH", best_offset, best_length))
                i += best_length
            else:
                output.append(0)
                output.append(data[i])
                i += 1

        return header + bytes(output)

    def decompress(self, blob: bytes) -> bytes:
        if len(blob) < 8:
            raise ValueError("无效的 LZ77 数据：长度不足")

        magic, original_length = struct.unpack(">4sI", blob[:8])
        if magic != self.MAGIC:
            raise ValueError("无效的 LZ77 数据：文件头不匹配")

        output = bytearray()
        i = 8
        n = len(blob)

        while i < n and len(output) < original_length:
            flag = blob[i]
            i += 1

            if flag == 0:
                if i >= n:
                    raise ValueError("无效的 LZ77 数据：字面量缺失")
                output.append(blob[i])
                i += 1

            elif flag == 1:
                if i + 4 > n:
                    raise ValueError("无效的 LZ77 数据：匹配项缺失")
                offset, length = struct.unpack(">HH", blob[i:i + 4])
                i += 4

                if offset == 0 or offset > len(output):
                    raise ValueError("无效的 LZ77 数据：offset 非法")

                # 允许重叠复制
                for _ in range(length):
                    output.append(output[-offset])

            else:
                raise ValueError(f"无效的 LZ77 数据：未知 flag {flag}")

        if len(output) != original_length:
            raise ValueError("LZ77 解压失败：恢复长度不正确")

        return bytes(output)

    def _match_length(self, data: bytes, src: int, cur: int, max_len: int) -> int:
        """
        为了保持实现简单，这里只在“已有窗口范围内”找匹配，
        不让匹配源越过当前 cur 位置。
        """
        length = 0
        while (
            length < max_len
            and src + length < cur
            and cur + length < len(data)
            and data[src + length] == data[cur + length]
        ):
            length += 1
        return length