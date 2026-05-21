import os


TEXT_EXTENSIONS = {".html", ".htm", ".css", ".js", ".json", ".txt", ".xml", ".svg"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
DOWNLOAD_SUFFIXES = (".下载", ".download", ".crdownload", ".part", ".tmp")


def normalize_extension_for_detection(filename: str) -> str:
    detection_name = filename
    lower_name = detection_name.lower()

    for suffix in DOWNLOAD_SUFFIXES:
        if lower_name.endswith(suffix):
            detection_name = detection_name[:-len(suffix)]
            break

    return os.path.splitext(detection_name)[1].lower()


def has_download_suffix(filename: str) -> bool:
    lower_name = filename.lower()
    return any(lower_name.endswith(suffix) for suffix in DOWNLOAD_SUFFIXES)


def detect_resource_type(file_path: str) -> str:
    ext = normalize_extension_for_detection(file_path)

    if ext in TEXT_EXTENSIONS:
        return "text"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    return "unsupported"
