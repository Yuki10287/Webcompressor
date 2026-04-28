import json
import os
import shutil
import time

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import (
    QDesktopServices, QColor, QBrush, QPainter, QPixmap
)
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QTableWidget, QTableWidgetItem,
    QMessageBox, QFrame, QGridLayout, QHeaderView,
    QGraphicsDropShadowEffect
)

from core.resource_manager import ResourceManager
from core.package_manager import PackageManager
from compress.image_compressor import ImageCompressor
from compress.text_bundle_compressor import TextBundleCompressor
from utils.file_utils import read_binary, write_binary, ensure_dir


class BackgroundWidget(QWidget):
    def __init__(self, bg_path: str):
        super().__init__()
        self.bg_path = bg_path
        self.bg_pixmap = QPixmap(bg_path) if os.path.exists(bg_path) else QPixmap()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        if not self.bg_pixmap.isNull():
            scaled = self.bg_pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            painter.fillRect(self.rect(), QColor("#c8b7d9"))



class InfoCard(QFrame):
    def __init__(self, title: str, value: str = "--"):
        super().__init__()
        self.setObjectName("infoCard")

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")

        self.value_label = QLabel(value)
        self.value_label.setObjectName("cardValue")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        self.setLayout(layout)


class GlassPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("glassPanel")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("网页压缩系统")
        self.resize(1280, 820)

        self.project = None
        self.resource_manager = ResourceManager()
        self.package_manager = PackageManager()
        self.image_compressor = ImageCompressor()
        self.text_bundle_compressor = TextBundleCompressor()

        self.text_bundle_enabled = False
        self.text_bundle_original_size = 0
        self.text_bundle_compressed_size = 0
        self.text_bundle_path = ""

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bg_path = os.path.join(project_root, "assets", "ui_bg.jpg")

        self.background = BackgroundWidget(bg_path)
        self.setCentralWidget(self.background)

        main_layout = QVBoxLayout(self.background)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(18)

        # 顶部标题区
        self.header_panel = GlassPanel()
        header_layout = QVBoxLayout(self.header_panel)
        header_layout.setContentsMargins(22, 18, 22, 18)
        header_layout.setSpacing(8)

        self.page_title = QLabel("WEB COMPRESSOR")
        self.page_title.setObjectName("pageTitle")

        self.page_subtitle = QLabel("Bundle • LZ77 • Huffman • Image Optimization")
        self.page_subtitle.setObjectName("pageSubtitle")

        self.root_dir_label = QLabel("当前目录：未选择网页目录")
        self.root_dir_label.setObjectName("pathLabel")

        header_layout.addWidget(self.page_title)
        header_layout.addWidget(self.page_subtitle)
        header_layout.addWidget(self.root_dir_label)

        # 按钮区
        self.button_panel = GlassPanel()
        button_layout = QHBoxLayout(self.button_panel)
        button_layout.setContentsMargins(16, 14, 16, 14)
        button_layout.setSpacing(12)

        self.scan_button = QPushButton("选择网页目录")
        self.scan_button.clicked.connect(self.select_directory)

        self.compress_button = QPushButton("开始压缩")
        self.compress_button.clicked.connect(self.compress_project)
        self.compress_button.setEnabled(False)

        self.restore_button = QPushButton("恢复解压")
        self.restore_button.clicked.connect(self.restore_project)

        self.open_page_button = QPushButton("打开恢复网页")
        self.open_page_button.clicked.connect(self.open_restored_page)

        self.open_restore_folder_button = QPushButton("打开恢复目录")
        self.open_restore_folder_button.clicked.connect(self.open_restore_folder)

        for btn in [
            self.scan_button,
            self.compress_button,
            self.restore_button,
            self.open_page_button,
            self.open_restore_folder_button,
        ]:
            button_layout.addWidget(btn)

        # 信息卡片区
        self.card_original = InfoCard("原始总大小")
        self.card_compressed = InfoCard("压缩后总大小")
        self.card_rate = InfoCard("总压缩率")
        self.card_text_bundle = InfoCard("文本 Bundle")

        cards_layout = QGridLayout()
        cards_layout.setHorizontalSpacing(14)
        cards_layout.setVerticalSpacing(14)
        cards_layout.addWidget(self.card_original, 0, 0)
        cards_layout.addWidget(self.card_compressed, 0, 1)
        cards_layout.addWidget(self.card_rate, 0, 2)
        cards_layout.addWidget(self.card_text_bundle, 0, 3)

        # 表格区
        self.table_panel = GlassPanel()
        table_layout = QVBoxLayout(self.table_panel)
        table_layout.setContentsMargins(14, 14, 14, 14)
        table_layout.setSpacing(12)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "文件名", "相对路径", "类型", "原始大小(B)",
            "尝试压缩大小(B)", "最终采用大小(B)", "策略"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.summary_label = QLabel("等待操作...")
        self.summary_label.setObjectName("summaryLabel")

        table_layout.addWidget(self.table)
        table_layout.addWidget(self.summary_label)

        main_layout.addWidget(self.header_panel)
        main_layout.addWidget(self.button_panel)
        main_layout.addLayout(cards_layout)
        main_layout.addWidget(self.table_panel)

        self.apply_shadow(self.header_panel)
        self.apply_shadow(self.button_panel)
        self.apply_shadow(self.table_panel)
        self.apply_shadow(self.card_original, blur=40, alpha=65)
        self.apply_shadow(self.card_compressed, blur=40, alpha=65)
        self.apply_shadow(self.card_rate, blur=40, alpha=65)
        self.apply_shadow(self.card_text_bundle, blur=40, alpha=65)

    def apply_shadow(self, widget, blur=55, alpha=55):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(blur)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(40, 20, 60, alpha))
        widget.setGraphicsEffect(shadow)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                color: #f7f4fb;
                font-size: 14px;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                background: transparent;
            }

            QFrame#glassPanel, QFrame#infoCard {
                background-color: rgba(255, 255, 255, 0.24);
                border: 1px solid rgba(255, 255, 255, 0.30);
                border-radius: 24px;
            }

            QLabel#pageTitle {
                font-size: 30px;
                font-weight: 700;
                color: rgba(255, 255, 255, 0.98);
                letter-spacing: 1px;
            }

            QLabel#pageSubtitle {
                font-size: 14px;
                color: rgba(250, 246, 255, 0.88);
            }

            QLabel#pathLabel {
                background-color: rgba(255, 255, 255, 0.18);
                border: 1px solid rgba(255, 255, 255, 0.26);
                border-radius: 14px;
                padding: 10px 12px;
                color: rgba(255, 255, 255, 0.98);
            }

            QLabel#summaryLabel {
                background-color: rgba(255, 255, 255, 0.20);
                border: 1px solid rgba(255, 255, 255, 0.28);
                border-radius: 14px;
                padding: 12px 14px;
                color: rgba(255, 255, 255, 0.98);
                font-weight: 600;
            }

            QLabel#cardTitle {
                color: rgba(244, 239, 255, 0.84);
                font-size: 13px;
            }

            QLabel#cardValue {
                color: rgba(255, 255, 255, 1.0);
                font-size: 22px;
                font-weight: 700;
            }

            QPushButton {
                background-color: rgba(255, 255, 255, 0.20);
                color: rgba(255, 255, 255, 1.0);
                border: 1px solid rgba(255, 255, 255, 0.28);
                border-radius: 16px;
                padding: 10px 18px;
                font-weight: 600;
                min-height: 18px;
            }

            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.28);
                border: 1px solid rgba(255, 255, 255, 0.38);
            }

            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.34);
            }

            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 0.10);
                color: rgba(255, 255, 255, 0.45);
                border: 1px solid rgba(255, 255, 255, 0.12);
            }

            QTableWidget {
                background-color: rgba(255, 255, 255, 0.18);
                border: none;
                border-radius: 18px;
                gridline-color: rgba(255, 255, 255, 0.12);
                alternate-background-color: rgba(255, 255, 255, 0.10);
                selection-background-color: rgba(255, 255, 255, 0.24);
                selection-color: white;
                color: rgba(255, 255, 255, 0.98);
            }

            QHeaderView::section {
                background-color: rgba(255, 255, 255, 0.20);
                color: rgba(255, 255, 255, 0.98);
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.14);
                padding: 10px;
                font-weight: 700;
            }
        """)

    def select_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "选择网页资源目录")
        if not folder:
            return

        self.project = self.resource_manager.scan_project(folder)

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
            items = [
                QTableWidgetItem(resource.file_name),
                QTableWidgetItem(resource.relative_path),
                QTableWidgetItem(resource.resource_type),
                QTableWidgetItem(str(resource.original_size))
            ]

            if self.text_bundle_enabled and resource.resource_type == "text":
                attempted_display = "bundle"
                compressed_display = "bundle"
            else:
                attempted_display = str(getattr(resource, "attempted_size", 0))
                compressed_display = str(resource.compressed_size)

            items.extend([
                QTableWidgetItem(attempted_display),
                QTableWidgetItem(compressed_display),
                QTableWidgetItem(resource.compression_strategy or "")
            ])

            for col, item in enumerate(items):
                self.table.setItem(row, col, item)

            self.colorize_row(row, resource)

    def colorize_row(self, row, resource):
        type_item = self.table.item(row, 2)
        strategy_item = self.table.item(row, 6)

        if resource.resource_type == "text":
            type_item.setForeground(QBrush(QColor(245, 240, 255)))
        elif resource.resource_type == "image":
            type_item.setForeground(QBrush(QColor(205, 240, 245)))
        else:
            type_item.setForeground(QBrush(QColor(220, 220, 220)))

        strategy = resource.compression_strategy or ""

        if "bundle_pre_lz77_huffman_text" in strategy:
            strategy_item.setForeground(QBrush(QColor("#ffffff")))
            strategy_item.setBackground(QBrush(QColor(180, 130, 210, 70)))
        elif "jpeg_quality" in strategy:
            strategy_item.setForeground(QBrush(QColor("#ffffff")))
            strategy_item.setBackground(QBrush(QColor(180, 120, 150, 80)))
        elif "png_optimize" in strategy:
            strategy_item.setForeground(QBrush(QColor("#ffffff")))
            strategy_item.setBackground(QBrush(QColor(120, 180, 190, 85)))
        elif "store_original" in strategy:
            strategy_item.setForeground(QBrush(QColor("#ffffff")))
            strategy_item.setBackground(QBrush(QColor(160, 160, 180, 70)))
        elif "skip" in strategy:
            strategy_item.setForeground(QBrush(QColor("#ffffff")))
            strategy_item.setBackground(QBrush(QColor(140, 140, 140, 60)))
        elif "error" in strategy:
            strategy_item.setForeground(QBrush(QColor("#ffffff")))
            strategy_item.setBackground(QBrush(QColor(180, 80, 110, 90)))

    def compress_project(self):
        if not self.project:
            QMessageBox.warning(self, "提示", "请先选择目录")
            return

        output_root = os.path.join("output", "compressed")
        bundle_output_root = os.path.join("output", "bundles")
        restored_bundle_root = os.path.join("output", "restored_bundle_text")

        ensure_dir(output_root)
        ensure_dir(bundle_output_root)
        ensure_dir(restored_bundle_root)

        manifest_files = []

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

                all_ok = True
                for relative_path, raw in files:
                    restored = restored_map.get(relative_path)
                    restore_target_path = os.path.join(restored_site_root, relative_path)

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
                self.text_bundle_enabled = False
                self.text_bundle_original_size = 0
                self.text_bundle_compressed_size = 0
                self.text_bundle_path = ""

                for resource in text_resources:
                    resource.compression_success = False
                    resource.compression_strategy = f"bundle_error: {e}"

        for resource in self.project.resources:
            if resource.resource_type != "image":
                continue

            try:
                original_data = read_binary(resource.file_path)

                start = time.perf_counter()
                compressed_data, image_strategy = self.image_compressor.compress(resource.file_path, quality=70)
                compress_time_ms = (time.perf_counter() - start) * 1000

                resource.attempted_size = len(compressed_data)

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

        for resource in self.project.resources:
            if resource.resource_type == "unsupported":
                resource.attempted_size = resource.original_size
                resource.compressed_size = resource.original_size
                resource.compression_strategy = "skip"
                resource.compression_success = True
                resource.restored_success = True

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

    def get_restore_root(self):
        manifest_path = os.path.join("output", "compressed", "manifest.json")
        if not os.path.exists(manifest_path):
            return None

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            project_root = manifest.get("project_root", "")
            site_name = os.path.basename(os.path.abspath(project_root)) if project_root else "restored_site"
            return os.path.join("output", "restored_from_package", site_name)
        except Exception:
            return None

    def get_restored_index_path(self):
        restore_root = self.get_restore_root()
        if not restore_root:
            return None

        index_path = os.path.join(restore_root, "index.html")
        if os.path.exists(index_path):
            return index_path
        return None

    def open_restored_page(self):
        index_path = self.get_restored_index_path()
        if not index_path:
            QMessageBox.warning(
                self,
                "提示",
                "未找到恢复后的 index.html。\n请先执行“恢复解压”，并确认恢复目录中存在首页。"
            )
            return

        url = QUrl.fromLocalFile(os.path.abspath(index_path))
        opened = QDesktopServices.openUrl(url)

        if not opened:
            QMessageBox.warning(self, "提示", f"尝试打开失败，请手动打开：\n{index_path}")

    def open_restore_folder(self):
        restore_root = self.get_restore_root()
        if not restore_root or not os.path.exists(restore_root):
            QMessageBox.warning(self, "提示", "未找到恢复目录，请先执行“恢复解压”。")
            return

        url = QUrl.fromLocalFile(os.path.abspath(restore_root))
        opened = QDesktopServices.openUrl(url)

        if not opened:
            QMessageBox.warning(self, "提示", f"尝试打开目录失败，请手动打开：\n{restore_root}")

    def restore_project(self):
        manifest_path = os.path.join("output", "compressed", "manifest.json")

        if not os.path.exists(manifest_path):
            QMessageBox.warning(self, "提示", "未找到 manifest.json，请先执行压缩。")
            return

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            project_root = manifest.get("project_root", "")
            site_name = os.path.basename(os.path.abspath(project_root)) if project_root else "restored_site"

            restore_root = os.path.join("output", "restored_from_package", site_name)
            ensure_dir(restore_root)

            if manifest.get("text_bundle_enabled"):
                bundle_path = manifest.get("text_bundle_path", "")
                if bundle_path and os.path.exists(bundle_path):
                    bundle_blob = read_binary(bundle_path)
                    restored_map = self.text_bundle_compressor.decompress_files(bundle_blob)

                    for relative_path, raw in restored_map.items():
                        target_path = os.path.join(restore_root, relative_path)
                        write_binary(target_path, raw)

            for item in manifest.get("files", []):
                if item.get("type") != "image":
                    continue

                compressed_path = item.get("compressed_path", "")
                relative_path = item.get("relative_path", "")

                if compressed_path and os.path.exists(compressed_path):
                    target_path = os.path.join(restore_root, relative_path)
                    ensure_dir(os.path.dirname(target_path))
                    shutil.copy2(compressed_path, target_path)

            index_path = os.path.join(restore_root, "index.html")
            if os.path.exists(index_path):
                reply = QMessageBox.question(
                    self,
                    "恢复完成",
                    f"恢复完成。\n恢复目录：{restore_root}\n\n是否立即打开恢复后的网页？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.open_restored_page()
            else:
                QMessageBox.information(
                    self,
                    "恢复完成",
                    f"恢复完成。\n恢复目录：{restore_root}\n未检测到 index.html，请手动检查。"
                )

        except Exception as e:
            QMessageBox.critical(self, "恢复失败", f"恢复解压时出错：{e}")

    def calculate_total_compressed_size(self):
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
            self.card_original.value_label.setText("--")
            self.card_compressed.value_label.setText("--")
            self.card_rate.value_label.setText("--")
            self.card_text_bundle.value_label.setText("--")
            return

        original_total = sum(r.original_size for r in self.project.resources)
        compressed_total = self.calculate_total_compressed_size()

        if original_total == 0:
            rate = 0.0
        else:
            rate = (original_total - compressed_total) / original_total * 100

        self.card_original.value_label.setText(f"{original_total} B")
        self.card_compressed.value_label.setText(f"{compressed_total} B")
        self.card_rate.value_label.setText(f"{rate:.2f}%")

        if self.text_bundle_enabled:
            self.card_text_bundle.value_label.setText(
                f"{self.text_bundle_original_size} → {self.text_bundle_compressed_size} B"
            )
            self.summary_label.setText(
                f"压缩完成：原始 {original_total} B，压缩后 {compressed_total} B，"
                f"压缩率 {rate:.2f}% | 文本采用整站 bundle"
            )
        else:
            self.card_text_bundle.value_label.setText("未启用")
            self.summary_label.setText(
                f"压缩完成：原始 {original_total} B，压缩后 {compressed_total} B，压缩率 {rate:.2f}%"
            )