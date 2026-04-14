from io import BytesIO
from PIL import Image


class ImageCompressor:
    strategy_name = "pillow_image"

    def compress(self, input_path: str, quality: int = 70) -> bytes:
        image = Image.open(input_path)
        buffer = BytesIO()

        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        return buffer.getvalue()