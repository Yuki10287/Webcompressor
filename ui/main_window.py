import os
import time

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QLabel, QTableWidget, QTableWidgetItem,
    QMessageBox
)

from core.resource_manager import ResourceManager
from core.package_manager import PackageManager
from core.validator import Validator
from compress.image_compressor import ImageCompressor
from compress.text_bundle_compressor import TextBundleCompressor
from utils.file_utils import read_binary, write_binary, ensure_dir


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("网页压缩系统")
        self.resize(1100, 650)

        self.project = None
        self.resource_manager = ResourceManager()
        self.package_manager = PackageManager()
        self.validator = Validator()
        self.image_compressor = ImageCompressor()
        self.text_bundle_compressor = TextBundleCompressor()

        # 文本 bundle 统计信息
        self.text_bundle_enabled = False
        self.text_bundle_original_size = 0
        self.text_bundle_compressed_size = 0
        self.text_bundle_path = ""

        self.root_dir_label = QLabel("未选择项目目录")
        self.summary_label = QLabel("等待操作...")

        self.scan_button = QPushButton("选择网页目录")
        self.scan_button.clicked.connect(self.select_directory)

        self.compress_button = QPushButton("开始压缩")
        self.compress_button.clicked.connect(self.compress_project)
        self.compress_button.setEnabled(False)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "文件名", "相对路径", "类型", "原始大小(B)",
            "尝试压缩大小(B)", "最终采用大小(B)", "策略"
        ])

        layout = QVBoxLayout()
        layout.addWidget(self.root_dir_label)
        layout.addWidget(self.scan_button)
        layout.addWidget(self.compress_button)
        layout.addWidget(self.table)
        layout.addWidget(self.summary_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def select_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "选择网页资源目录")
        if not folder:
            return

        self.project = self.resource_manager.scan_project(folder)

        # 重置 bundle 统计
        self.text_bundle_enabled = False
        self.text_bundle_original_size = 0
        self.text_bundle_compressed_size = 0
        self.text_bundle_path = ""

        self.root_dir_label.setText(f"当前目录：{folder}")
        self.compress_button.setEnabled(True)
        self.refresh_table()
        self.update_summary_label()

    def refresh_table(self):
        if not self.project:
            return

        self.table.setRowCount(len(self.project.resources))

        for row, resource in enumerate(self.project.resources):
            self.table.setItem(row, 0, QTableWidgetItem(resource.file_name))
            self.table.setItem(row, 1, QTableWidgetItem(resource.relative_path))
            self.table.setItem(row, 2, QTableWidgetItem(resource.resource_type))
            self.table.setItem(row, 3, QTableWidgetItem(str(resource.original_size)))

            # 文本资源如果启用了 bundle，则表格里显示为 bundle 模式
            if self.text_bundle_enabled and resource.resource_type == "text":
                attempted_display = "bundle"
                compressed_display = "bundle"
            else:
                attempted_display = str(getattr(resource, "attempted_size", 0))
                compressed_display = str(resource.compressed_size)

            self.table.setItem(row, 4, QTableWidgetItem(attempted_display))
            self.table.setItem(row, 5, QTableWidgetItem(compressed_display))
            self.table.setItem(row, 6, QTableWidgetItem(resource.compression_strategy or ""))

    def compress_project(self):
        if not self.project:
            QMessageBox.warning(self, "提示", "请先选择目录")
            return

        output_root = os.path.join("output", "compressed")
        restored_root = os.path.join("output", "restored")
        bundle_output_root = os.path.join("output", "bundles")
        restored_bundle_root = os.path.join("output", "restored_bundle_text")

        ensure_dir(output_root)
        ensure_dir(restored_root)
        ensure_dir(bundle_output_root)
        ensure_dir(restored_bundle_root)

        manifest_files = []

        # -------------------------------------------------
        # 1) 先处理文本：整站 bundle 压缩
        # -------------------------------------------------
        text_resources = [r for r in self.project.resources if r.resource_type == "text"]

        self.text_bundle_enabled = False
        self.text_bundle_original_size = 0
        self.text_bundle_compressed_size = 0
        self.text_bundle_path = ""

        if text_resources:
            files = []
            site_name = os.path.basename(os.path.abspath(self.project.root_dir))
            restored_site_root = os.path.join(restored_bundle_root, site_name)

            for resource in text_resources:
                raw = read_binary(resource.file_path)
                normalized_path = resource.relative_path.replace("\\", "/")
                files.append((normalized_path, raw))
                self.text_bundle_original_size += len(raw)

            try:
                bundle_blob = self.text_bundle_compressor.compress_files(files)
                restored_map = self.text_bundle_compressor.decompress_files(bundle_blob)

                # 校验与输出恢复文件
                all_ok = True
                for relative_path, raw in files:
                    restored = restored_map.get(relative_path)

                    normalized_relative = relative_path.replace("\\", "/")
                    restore_target_path = os.path.join(restored_site_root, normalized_relative)
                    if restored is not None:
                        write_binary(restore_target_path, restored)

                    if restored != raw:
                        all_ok = False

                bundle_path = os.path.join(bundle_output_root, f"{site_name}_text_bundle.bin")
                write_binary(bundle_path, bundle_blob)

                self.text_bundle_enabled = True
                self.text_bundle_compressed_size = len(bundle_blob)
                self.text_bundle_path = bundle_path

                for resource in text_resources:
                    resource.attempted_size = len(bundle_blob)
                    resource.compressed_size = 0
                    resource.compression_strategy = "bundle_pre_lz77_huffman_text"
                    resource.compression_success = True
                    resource.restored_success = all_ok

                    manifest_files.append({
                        "relative_path": resource.relative_path.replace("\\", "/"),
                        "type": resource.resource_type,
                        "strategy": resource.compression_strategy,
                        "bundle_path": bundle_path,
                        "restored_success": all_ok
                    })

            except Exception as e:
                # 如果 bundle 失败，则文本统一标记失败
                self.text_bundle_enabled = False
                self.text_bundle_original_size = 0
                self.text_bundle_compressed_size = 0
                self.text_bundle_path = ""

                for resource in text_resources:
                    resource.compression_success = False
                    resource.compression_strategy = f"bundle_error: {e}"

        # -------------------------------------------------
        # 2) 再处理图片：逐文件压缩
        # -------------------------------------------------
        for resource in self.project.resources:
            if resource.resource_type != "image":
                continue

            try:
                original_data = read_binary(resource.file_path)

                start = time.perf_counter()
                compressed_data, image_strategy = self.image_compressor.compress(resource.file_path, quality=70)
                compress_time_ms = (time.perf_counter() - start) * 1000

                resource.attempted_size = len(compressed_data)

                # 若压缩后更大，则保留原图
                if len(compressed_data) >= len(original_data):
                    compressed_data = original_data
                    strategy = "store_original_image"
                    suffix = os.path.splitext(resource.file_path)[1]
                else:
                    strategy = image_strategy
                    if image_strategy == "jpeg_quality":
                        suffix = ".jpg"
                    elif image_strategy == "png_optimize":
                        suffix = ".png"
                    else:
                        suffix = os.path.splitext(resource.file_path)[1]

                compressed_path = self.package_manager.save_compressed_file(
                    output_root, resource.relative_path, compressed_data, suffix
                )

                resource.compressed_size = len(compressed_data)
                resource.compression_strategy = strategy
                resource.compression_success = True
                resource.restored_success = True

                manifest_files.append({
                    "relative_path": resource.relative_path.replace("\\", "/"),
                    "type": resource.resource_type,
                    "strategy": resource.compression_strategy,
                    "compressed_path": compressed_path,
                    "restored_success": True,
                    "compress_time_ms": round(compress_time_ms, 3)
                })

            except Exception as e:
                resource.compression_success = False
                resource.compression_strategy = f"error: {e}"

        # -------------------------------------------------
        # 3) 不支持的文件直接跳过
        # -------------------------------------------------
        for resource in self.project.resources:
            if resource.resource_type == "unsupported":
                resource.attempted_size = resource.original_size
                resource.compressed_size = resource.original_size
                resource.compression_strategy = "skip"
                resource.compression_success = True
                resource.restored_success = True

        # -------------------------------------------------
        # 4) 保存 manifest
        # -------------------------------------------------
        self.package_manager.save_manifest(output_root, {
            "project_root": self.project.root_dir,
            "text_bundle_enabled": self.text_bundle_enabled,
            "text_bundle_original_size": self.text_bundle_original_size,
            "text_bundle_compressed_size": self.text_bundle_compressed_size,
            "text_bundle_path": self.text_bundle_path,
            "files": manifest_files
        })

        self.refresh_table()
        self.update_summary_label()
        QMessageBox.information(self, "完成", "压缩完成")

    def calculate_total_compressed_size(self) -> int:
        if not self.project:
            return 0

        total = 0

        for resource in self.project.resources:
            if resource.resource_type == "text":
                continue

            if resource.compressed_size > 0:
                total += resource.compressed_size
            else:
                total += resource.original_size

        if self.text_bundle_enabled:
            total += self.text_bundle_compressed_size
        else:
            for resource in self.project.resources:
                if resource.resource_type == "text":
                    if resource.compressed_size > 0:
                        total += resource.compressed_size
                    else:
                        total += resource.original_size

        return total

    def update_summary_label(self):
        if not self.project:
            self.summary_label.setText("等待操作...")
            return

        original_total = sum(r.original_size for r in self.project.resources)
        compressed_total = self.calculate_total_compressed_size()

        if original_total == 0:
            rate = 0.0
        else:
            rate = (original_total - compressed_total) / original_total * 100

        if self.text_bundle_enabled:
            self.summary_label.setText(
                f"压缩完成：原始 {original_total} B，压缩后 {compressed_total} B，"
                f"压缩率 {rate:.2f}% | 文本采用整站 bundle："
                f"{self.text_bundle_original_size} B -> {self.text_bundle_compressed_size} B"
            )
        else:
            self.summary_label.setText(
                f"压缩完成：原始 {original_total} B，压缩后 {compressed_total} B，压缩率 {rate:.2f}%"
            )