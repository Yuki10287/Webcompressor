import os


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def get_file_size(path: str) -> int:
    return os.path.getsize(path)


def read_binary(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def write_binary(path: str, data: bytes) -> None:
    parent = os.path.dirname(path)
    if parent:
        ensure_dir(parent)
    with open(path, "wb") as f:
        f.write(data)