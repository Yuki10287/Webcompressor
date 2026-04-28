import struct


class LZ77Codec:
    MAGIC = b"LZ77"

    def __init__(self, window_size: int = 8192, lookahead_size: int = 127, min_match: int = 4):
        """
        window_size: 滑动窗口大小
        lookahead_size: 前瞻缓冲区大小（这里控制在 255 以内，便于用 1 字节存长度）
        min_match: 最小匹配长度
        """
        self.window_size = window_size
        self.lookahead_size = lookahead_size
        self.min_match = min_match

    def compress(self, data: bytes) -> bytes:
        """
        输出格式：
        MAGIC(4) + original_length(4) + token_stream

        token_stream:
        - 字面量: flag=0 + byte(1)                      共 2 字节
        - 匹配项: flag=1 + offset(2) + length(1)       共 4 字节

        相比旧版：
        - length 从 2 字节缩成 1 字节
        - token 更紧凑
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

            # 从近到远搜索，通常更容易先找到更优匹配
            for j in range(i - 1, window_start - 1, -1):
                offset = i - j
                match_len = self._match_length(data, j, i, max_len)

                if match_len > best_length:
                    best_length = match_len
                    best_offset = offset

                    if best_length == max_len:
                        break

            if best_length >= self.min_match:
                output.append(1)
                output.extend(struct.pack(">HB", best_offset, best_length))
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
                if i + 3 > n:
                    raise ValueError("无效的 LZ77 数据：匹配项缺失")

                offset, length = struct.unpack(">HB", blob[i:i + 3])
                i += 3

                if offset == 0 or offset > len(output):
                    raise ValueError("无效的 LZ77 数据：offset 非法")

                # 允许重叠复制，这才更符合 LZ77 的行为
                for _ in range(length):
                    output.append(output[-offset])

            else:
                raise ValueError(f"无效的 LZ77 数据：未知 flag {flag}")

        if len(output) != original_length:
            raise ValueError("LZ77 解压失败：恢复长度不正确")

        return bytes(output)

    def _match_length(self, data: bytes, src: int, cur: int, max_len: int) -> int:
        """
        支持重叠匹配。
        例如 offset 很小时，可以匹配 aaa... 这种重复串。
        """
        offset = cur - src
        if offset <= 0:
            return 0

        length = 0
        n = len(data)

        while length < max_len and (cur + length) < n:
            # 当 length 超过 offset 后，匹配源进入“重叠复制”阶段
            if src + length < cur:
                left_byte = data[src + length]
            else:
                left_byte = data[src + (length % offset)]

            right_byte = data[cur + length]

            if left_byte != right_byte:
                break

            length += 1

        return length