import os
import time

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QLabel, QTableWidget, QTableWidgetItem,
    QMessageBox
)

from core.resource_manager import ResourceManager
from core.analyzer import Analyzer
from core.package_manager import PackageManager
from core.validator import Validator
from compress.text_compressor import TextCompressor
from compress.image_compressor import ImageCompressor
from utils.file_utils import read_binary, write_binary, ensure_dir


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("网页压缩系统")
        self.resize(900, 600)

        self.project = None
        self.resource_manager = ResourceManager()
        self.analyzer = Analyzer()
        self.package_manager = PackageManager()
        self.validator = Validator()
        self.text_compressor = TextCompressor()
        self.image_compressor = ImageCompressor()

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
        self.root_dir_label.setText(f"当前目录：{folder}")
        self.compress_button.setEnabled(True)
        self.refresh_table()

        summary = self.analyzer.summarize(self.project)
        self.summary_label.setText(
            f"扫描完成：共 {summary['file_count']} 个文件，原始大小 {summary['original_size']} B"
        )

    def refresh_table(self):
        if not self.project:
            return

        self.table.setRowCount(len(self.project.resources))
        for row, resource in enumerate(self.project.resources):
            self.table.setItem(row, 0, QTableWidgetItem(resource.file_name))
            self.table.setItem(row, 1, QTableWidgetItem(resource.relative_path))
            self.table.setItem(row, 2, QTableWidgetItem(resource.resource_type))
            self.table.setItem(row, 3, QTableWidgetItem(str(resource.original_size)))
            self.table.setItem(row, 4, QTableWidgetItem(str(resource.attempted_size)))
            self.table.setItem(row, 5, QTableWidgetItem(str(resource.compressed_size)))
            self.table.setItem(row, 6, QTableWidgetItem(resource.compression_strategy or ""))

    def compress_project(self):
        if not self.project:
            QMessageBox.warning(self, "提示", "请先选择目录")
            return

        output_root = os.path.join("output", "compressed")
        restored_root = os.path.join("output", "restored")
        ensure_dir(output_root)
        ensure_dir(restored_root)

        manifest_files = []

        for resource in self.project.resources:
            try:
                if resource.resource_type == "text":
                    original_data = read_binary(resource.file_path)

                    start = time.perf_counter()
                    huffman_data = self.text_compressor.compress(original_data, resource.file_path)
                    compress_time_ms = (time.perf_counter() - start) * 1000

                    # 新增：记录“尝试压缩后大小”
                    resource.attempted_size = len(huffman_data)

                    # 如果压缩后更大，则直接保留原文件
                    if len(huffman_data) >= len(original_data):
                        compressed_data = original_data
                        strategy = "store_original_text"
                    else:
                        compressed_data = huffman_data
                        strategy = self.text_compressor.strategy_name

                    compressed_path = self.package_manager.save_compressed_file(
                        output_root, resource.relative_path, compressed_data, ".bin"
                    )

                    # 只有真正压缩过才解压，否则直接认为恢复成功
                    if strategy == self.text_compressor.strategy_name:
                        restored_data = self.text_compressor.decompress(compressed_data)
                    else:
                        restored_data = original_data

                    restored_ok = self.validator.validate_bytes_equal(original_data, restored_data)

                    restored_path = os.path.join(restored_root, resource.relative_path)
                    write_binary(restored_path, restored_data)

                    resource.compressed_size = len(compressed_data)
                    resource.compression_strategy = strategy
                    resource.compression_success = True
                    resource.restored_success = restored_ok

                    manifest_files.append({
                        "relative_path": resource.relative_path,
                        "type": resource.resource_type,
                        "strategy": resource.compression_strategy,
                        "compressed_path": compressed_path,
                        "restored_success": restored_ok,
                        "compress_time_ms": round(compress_time_ms, 3)
                    })

                elif resource.resource_type == "image":
                    original_data = read_binary(resource.file_path)

                    start = time.perf_counter()
                    compressed_data, image_strategy = self.image_compressor.compress(resource.file_path, quality=70)
                    compress_time_ms = (time.perf_counter() - start) * 1000
                    resource.attempted_size = len(compressed_data)
                    # 如果压缩后更大，则直接保留原图
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
                        "relative_path": resource.relative_path,
                        "type": resource.resource_type,
                        "strategy": resource.compression_strategy,
                        "compressed_path": compressed_path,
                        "restored_success": True,
                        "compress_time_ms": round(compress_time_ms, 3)
                    })

                else:
                    resource.compression_strategy = "skip"
                    resource.compressed_size = resource.original_size

            except Exception as e:
                resource.compression_success = False
                resource.compression_strategy = f"error: {e}"

        self.package_manager.save_manifest(output_root, {
            "project_root": self.project.root_dir,
            "files": manifest_files
        })

        self.refresh_table()
        summary = self.analyzer.summarize(self.project)
        self.summary_label.setText(
            f"压缩完成：原始 {summary['original_size']} B，压缩后 {summary['compressed_size']} B，压缩率 {summary['compression_rate']}%"
        )
        QMessageBox.information(self, "完成", "压缩完成")