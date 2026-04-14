from dataclasses import dataclass, field
from typing import List
from models.resource_file import ResourceFile


@dataclass
class WebProject:
    root_dir: str
    resources: List[ResourceFile] = field(default_factory=list)

    @property
    def total_original_size(self) -> int:
        return sum(r.original_size for r in self.resources)

    @property
    def total_compressed_size(self) -> int:
        return sum(r.compressed_size for r in self.resources)

    @property
    def compression_rate(self) -> float:
        if self.total_original_size == 0:
            return 0.0
        return (self.total_original_size - self.total_compressed_size) / self.total_original_size * 100