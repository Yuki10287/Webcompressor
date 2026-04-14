from models.web_project import WebProject


class Analyzer:
    def summarize(self, project: WebProject) -> dict:
        return {
            "file_count": len(project.resources),
            "original_size": project.total_original_size,
            "compressed_size": project.total_compressed_size,
            "compression_rate": round(project.compression_rate, 2),
        }