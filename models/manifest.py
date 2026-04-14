from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Manifest:
    project_root: str
    files: List[Dict] = field(default_factory=list)