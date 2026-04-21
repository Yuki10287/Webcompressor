import os
from io import BytesIO
from PIL import Image


class ImageCompressor:
    strategy_name = "adaptive_image"

    def compress(self, input_path: str, quality: int = 70) -> tuple[bytes, str]:
        ext = os.path.splitext(input_path)[1].lower()
        image = Image.open(input_path)
        buffer = BytesIO()

        # JPEG：做质量压缩
        if ext in [".jpg", ".jpeg"]:
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            image.save(buffer, format="JPEG", quality=quality, optimize=True)
            return buffer.getvalue(), "jpeg_quality"

        # PNG：保留 PNG 格式，做无损优化
        elif ext == ".png":
            image.save(buffer, format="PNG", optimize=True)
            return buffer.getvalue(), "png_optimize"

        # 其他图片类型暂时原样返回
        else:
            with open(input_path, "rb") as f:
                return f.read(), "store_original"