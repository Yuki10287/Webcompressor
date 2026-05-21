from typing import Dict, List, Tuple

from core.type_detector import normalize_extension_for_detection


MARKER = 0xFF
ESCAPE_CODE = 0


class DictionaryPreprocessor:
    def __init__(self, patterns: List[bytes]):
        # 去重，并按长度从长到短排序，优先替换长片段
        unique_patterns = sorted(set(patterns), key=len, reverse=True)

        if len(unique_patterns) > 200:
            raise ValueError("预处理模式过多，建议控制在 200 个以内")

        self.patterns = unique_patterns
        self.code_to_pattern: Dict[int, bytes] = {}
        self.pattern_to_code: Dict[bytes, int] = {}

        code = 1
        for p in self.patterns:
            self.code_to_pattern[code] = p
            self.pattern_to_code[p] = code
            code += 1

    def preprocess(self, data: bytes) -> bytes:
        # 先转义 marker 本身，避免和 token 冲突
        data = data.replace(bytes([MARKER]), bytes([MARKER, ESCAPE_CODE]))

        # 再做高频片段替换
        for pattern in self.patterns:
            token = bytes([MARKER, self.pattern_to_code[pattern]])
            data = data.replace(pattern, token)

        return data

    def restore(self, data: bytes) -> bytes:
        result = bytearray()
        i = 0
        n = len(data)

        while i < n:
            b = data[i]
            if b != MARKER:
                result.append(b)
                i += 1
                continue

            if i + 1 >= n:
                raise ValueError("预处理恢复失败：marker 后缺少编码字节")

            code = data[i + 1]

            if code == ESCAPE_CODE:
                result.append(MARKER)
            else:
                pattern = self.code_to_pattern.get(code)
                if pattern is None:
                    raise ValueError(f"预处理恢复失败：未知 token 编码 {code}")
                result.extend(pattern)

            i += 2

        return bytes(result)


HTML_PATTERNS = [
    b'<meta charset="UTF-8">',
    b'<link rel="stylesheet" href="',
    b'<script src="',
    b'</script>',
    b'</body>',
    b'</html>',
    b'</head>',
    b'<body>',
    b'<head>',
    b'</div>',
    b'<div ',
    b'<div>',
    b'<html',
    b'class=',
    b'href=',
    b'src=',
    b'alt=',
    b'<img ',
    b'</p>',
    b'<p>',
]

CSS_PATTERNS = [
    b'background-color',
    b'font-family',
    b'box-shadow',
    b'border-radius',
    b'line-height',
    b'padding',
    b'margin',
    b'color',
    b'width',
    b'height',
    b'display',
    b'justify-content',
    b'align-items',
    b'position',
    b'font-size',
    b'px',
    b'rgba(',
    b'#{',
    b' {',
    b';\n',
]

JS_PATTERNS = [
    b'function ',
    b'return ',
    b'const ',
    b'let ',
    b'var ',
    b'console.',
    b'document.',
    b'getElementById',
    b'addEventListener',
    b'querySelector',
    b'querySelectorAll',
    b'window.',
    b');',
    b'()',
    b' {',
    b'}\n',
]


class TextPreprocessorManager:
    TYPE_PLAIN = 0
    TYPE_HTML = 1
    TYPE_CSS = 2
    TYPE_JS = 3

    def __init__(self):
        self.html_pre = DictionaryPreprocessor(HTML_PATTERNS)
        self.css_pre = DictionaryPreprocessor(CSS_PATTERNS)
        self.js_pre = DictionaryPreprocessor(JS_PATTERNS)

    def preprocess_by_path(self, file_path: str, data: bytes) -> Tuple[int, bytes]:
        ext = normalize_extension_for_detection(file_path)

        if ext in [".html", ".htm"]:
            return self.TYPE_HTML, self.html_pre.preprocess(data)
        if ext == ".css":
            return self.TYPE_CSS, self.css_pre.preprocess(data)
        if ext == ".js":
            return self.TYPE_JS, self.js_pre.preprocess(data)

        return self.TYPE_PLAIN, data

    def restore_by_type(self, type_id: int, data: bytes) -> bytes:
        if type_id == self.TYPE_HTML:
            return self.html_pre.restore(data)
        if type_id == self.TYPE_CSS:
            return self.css_pre.restore(data)
        if type_id == self.TYPE_JS:
            return self.js_pre.restore(data)
        return data
