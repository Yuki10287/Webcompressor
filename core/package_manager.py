import json
import os
from utils.file_utils import ensure_dir, write_binary


class PackageManager:
    def save_compressed_file(self, output_root: str, relative_path: str, data: bytes, suffix: str) -> str:
        target_path = os.path.join(output_root, relative_path + suffix)
        write_binary(target_path, data)
        return target_path

    def save_manifest(self, output_root: str, manifest_data: dict) -> str:
        ensure_dir(output_root)
        manifest_path = os.path.join(output_root, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, ensure_ascii=False, indent=2)
        return manifest_path