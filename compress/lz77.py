import struct


class LZ77Codec:
    """
    LZ77 编解码器。

    压缩端输出两类 token：字面量和匹配项。匹配项保存 offset 和 length，
    表示“从已经输出过的数据中向前回看 offset 个字节，复制 length 个字节”。

    这里的优化只改变匹配搜索方式：用短片段哈希索引快速找到候选位置，
    输出格式和解压逻辑仍然是标准 LZ77 思路。
    """

    MAGIC = b"LZ77"

    def __init__(
        self,
        window_size: int = 8192,
        lookahead_size: int = 127,
        min_match: int = 4,
        max_candidates: int = 64
    ):
        """
        window_size: 滑动窗口大小
        lookahead_size: 前瞻缓冲区大小（这里控制在 255 以内，便于用 1 字节存长度）
        min_match: 最小匹配长度
        max_candidates: 每个位置最多比较的候选匹配数
        """
        self.window_size = window_size
        self.lookahead_size = lookahead_size
        self.min_match = min_match
        self.max_candidates = max_candidates

    def compress(self, data: bytes) -> bytes:
        """
        输出格式：
        MAGIC(4) + original_length(4) + token_stream

        token_stream:
        - 字面量: flag=0 + byte(1)                      共 2 字节
        - 匹配项: flag=1 + offset(2) + length(1)       共 4 字节
        """
        header = struct.pack(">4sI", self.MAGIC, len(data))
        output = bytearray()

        i = 0
        n = len(data)
        position_index = {}
        next_index_pos = 0

        while i < n:
            # position_index 只登记当前位置之前的数据，避免匹配到未来内容。
            while next_index_pos < i:
                self._add_index_position(position_index, data, next_index_pos, n)
                next_index_pos += 1

            best_offset = 0
            best_length = 0

            window_start = max(0, i - self.window_size)
            max_len = min(self.lookahead_size, n - i)

            if max_len >= self.min_match:
                # 用当前位置开头的 min_match 字节做 key，只比较相同前缀的历史位置。
                key = data[i:i + self.min_match]
                candidates = position_index.get(key, [])
                checked = 0

                # 从最近的候选开始尝试。网页文本的重复片段通常离当前位置较近。
                for j in reversed(candidates):
                    if j < window_start:
                        break

                    offset = i - j
                    match_len = self._match_length(data, j, i, max_len)
                    checked += 1

                    if match_len > best_length:
                        best_length = match_len
                        best_offset = offset

                        if best_length == max_len:
                            break

                    if checked >= self.max_candidates:
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

    def _add_index_position(self, position_index: dict, data: bytes, pos: int, data_len: int) -> None:
        """把历史位置加入哈希索引，供后续位置快速查找候选匹配。"""
        if pos + self.min_match > data_len:
            return

        key = data[pos:pos + self.min_match]
        positions = position_index.setdefault(key, [])
        positions.append(pos)

        # 限制每个 key 保留的位置数量，防止极端重复文本让候选表无限膨胀。
        if len(positions) > self.max_candidates * 8:
            del positions[:self.max_candidates * 4]

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
