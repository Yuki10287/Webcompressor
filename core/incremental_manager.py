import hashlib
import json
import os
from typing import Dict, List, Optional


class IncrementalManager:
    """Detect file changes for incremental compression.

    This manager only tracks resource states. It does not run or change any
    compression algorithm, so callers can decide which changed files need to be
    compressed again.
    """

    def __init__(self, cache_root: Optional[str] = None):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cache_root = cache_root or os.path.join(
            project_root, "output", "incremental_cache"
        )

    def get_site_name(self, site_root: str) -> str:
        """Use the web directory name as the cache file prefix."""
        return os.path.basename(os.path.abspath(site_root.rstrip(os.sep)))

    def get_cache_path(self, site_root: str) -> str:
        site_name = self.get_site_name(site_root)
        return os.path.join(self.cache_root, f"{site_name}_state.json")

    def scan_site(self, site_root: str) -> Dict[str, Dict[str, object]]:
        """Scan all files under a site directory and return state by path."""
        site_root = os.path.abspath(site_root)
        states: Dict[str, Dict[str, object]] = {}

        for current_root, _, files in os.walk(site_root):
            for file_name in files:
                file_path = os.path.join(current_root, file_name)
                relative_path = self._normalize_relative_path(file_path, site_root)

                states[relative_path] = {
                    "relative_path": relative_path,
                    "size": os.path.getsize(file_path),
                    "mtime": os.path.getmtime(file_path),
                    "md5": self._calculate_md5(file_path),
                }

        return dict(sorted(states.items()))

    def load_state(self, site_root: str) -> Dict[str, Dict[str, object]]:
        """Load previous state. Missing cache means an empty old state."""
        cache_path = self.get_cache_path(site_root)
        if not os.path.exists(cache_path):
            return {}

        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        files = data.get("files", {})
        return dict(sorted(files.items()))

    def save_state(self, site_root: str, state: Dict[str, Dict[str, object]]) -> None:
        """Persist current state as UTF-8 JSON."""
        os.makedirs(self.cache_root, exist_ok=True)
        cache_path = self.get_cache_path(site_root)

        data = {
            "site_name": self.get_site_name(site_root),
            "site_root": os.path.abspath(site_root),
            "files": dict(sorted(state.items())),
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def detect_changes(
        self,
        site_root: str,
        update_cache: bool = True,
    ) -> Dict[str, List[str]]:
        """Compare current scan with cached state and return changed groups."""
        old_state = self.load_state(site_root)
        current_state = self.scan_site(site_root)
        result = self.compare_states(old_state, current_state)

        if update_cache:
            self.save_state(site_root, current_state)

        return result

    def compare_states(
        self,
        old_state: Dict[str, Dict[str, object]],
        current_state: Dict[str, Dict[str, object]],
    ) -> Dict[str, List[str]]:
        """Classify files as new, modified, unchanged, or deleted."""
        new_files: List[str] = []
        modified_files: List[str] = []
        unchanged_files: List[str] = []
        deleted_files: List[str] = []

        old_paths = set(old_state.keys())
        current_paths = set(current_state.keys())

        for relative_path in sorted(current_paths):
            if relative_path not in old_state:
                new_files.append(relative_path)
                continue

            old_file = old_state[relative_path]
            current_file = current_state[relative_path]

            # MD5 is the primary signal. Size and mtime are kept as auxiliary
            # metadata for reporting and for compatibility with older caches.
            if self._is_modified(old_file, current_file):
                modified_files.append(relative_path)
            else:
                unchanged_files.append(relative_path)

        for relative_path in sorted(old_paths - current_paths):
            deleted_files.append(relative_path)

        return {
            "new_files": new_files,
            "modified_files": modified_files,
            "unchanged_files": unchanged_files,
            "deleted_files": deleted_files,
        }

    def _is_modified(
        self,
        old_file: Dict[str, object],
        current_file: Dict[str, object],
    ) -> bool:
        old_md5 = old_file.get("md5")
        current_md5 = current_file.get("md5")

        if old_md5 and current_md5:
            return old_md5 != current_md5

        return (
            old_file.get("size") != current_file.get("size")
            or old_file.get("mtime") != current_file.get("mtime")
        )

    def _normalize_relative_path(self, file_path: str, site_root: str) -> str:
        relative_path = os.path.relpath(file_path, site_root)
        return relative_path.replace(os.sep, "/")

    def _calculate_md5(self, file_path: str) -> str:
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                md5.update(chunk)
        return md5.hexdigest()
