import os
from models.resource_file import ResourceFile
from models.web_project import WebProject
from core.type_detector import detect_resource_type


SKIP_FILES = {".gitkeep", ".DS_Store", "Thumbs.db"}


class ResourceManager:
    def scan_project(self, root_dir: str) -> WebProject:
        project = WebProject(root_dir=root_dir)

        for current_root, _, files in os.walk(root_dir):
            for file_name in files:
                if file_name in SKIP_FILES:
                    continue

                file_path = os.path.join(current_root, file_name)
                relative_path = os.path.relpath(file_path, root_dir)
                resource_type = detect_resource_type(file_path)
                original_size = os.path.getsize(file_path)

                resource = ResourceFile(
                    file_path=file_path,
                    relative_path=relative_path,
                    file_name=file_name,
                    resource_type=resource_type,
                    original_size=original_size
                )
                project.resources.append(resource)

        return project