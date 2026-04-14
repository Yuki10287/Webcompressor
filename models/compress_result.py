from dataclasses import dataclass


@dataclass
class CompressResult:
    file_path: str
    original_size: int
    compressed_size: int
    compress_time_ms: float
    decompress_time_ms: float = 0.0
    strategy: str = ""
    success: bool = False