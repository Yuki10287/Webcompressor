from dataclasses import dataclass
from typing import Optional


@dataclass
class ResourceFile:
    file_path: str
    relative_path: str
    file_name: str
    resource_type: str
    original_size: int
    compressed_size: int = 0
    attempted_size: int = 0
    compression_strategy: Optional[str] = None
    compression_success: bool = False
    restored_success: bool = False