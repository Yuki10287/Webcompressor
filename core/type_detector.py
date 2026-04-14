import os


TEXT_EXTENSIONS = {".html", ".htm", ".css", ".js", ".txt"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def detect_resource_type(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext in TEXT_EXTENSIONS:
        return "text"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    return "unsupported"