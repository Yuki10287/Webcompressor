import csv
import io
import os
import sys
import tarfile
import time
import zipfile
from typing import Dict, List, Tuple


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from core.resource_manager import ResourceManager
from compress.image_compressor import ImageCompressor
from compress.text_bundle_compressor import TextBundleCompressor
from utils.file_utils import ensure_dir, read_binary


SAMPLE_SITES = [
    os.path.join(PROJECT_ROOT, "sample_data", "demo_site"),
    os.path.join(PROJECT_ROOT, "sample_data", "benchmark_site_basic"),
    os.path.join(PROJECT_ROOT, "sample_data", "benchmark_site_rich"),
]


NETWORK_PROFILES = {
    "4G_10Mbps": 10,
    "WiFi_50Mbps": 50,
    "5G_200Mbps": 200,
}


def calc_rate(original_size: int, compressed_size: int) -> float:
    if original_size <= 0:
        return 0.0
    return (original_size - compressed_size) / original_size * 100.0


def bytes_to_transfer_seconds(size_bytes: int, bandwidth_mbps: float) -> float:
    """
    Mbps = megabits per second
    传输时间 = 字节数 * 8 / (Mbps * 1,000,000)
    """
    if bandwidth_mbps <= 0:
        return 0.0
    return size_bytes * 8 / (bandwidth_mbps * 1_000_000)


def collect_all_files(site_root: str) -> List[Tuple[str, str]]:
    """
    返回 [(absolute_path, relative_path), ...]
    """
    files = []
    for root, _, filenames in os.walk(site_root):
        for filename in filenames:
            abs_path = os.path.join(root, filename)
            rel_path = os.path.relpath(abs_path, site_root).replace("\\", "/")
            files.append((abs_path, rel_path))
    return files


def build_zip_bytes(site_root: str) -> bytes:
    """
    用 Python 标准库 zipfile 生成 ZIP 压缩包。
    """
    buffer = io.BytesIO()
    all_files = collect_all_files(site_root)

    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for abs_path, rel_path in all_files:
            zf.write(abs_path, rel_path)

    return buffer.getvalue()


def decompress_zip_bytes(zip_blob: bytes) -> int:
    """
    解压 ZIP 到内存，不落盘。返回解出的文件数量。
    """
    count = 0
    buffer = io.BytesIO(zip_blob)

    with zipfile.ZipFile(buffer, "r") as zf:
        for name in zf.namelist():
            if not name.endswith("/"):
                _ = zf.read(name)
                count += 1

    return count


def build_tar_gzip_bytes(site_root: str) -> bytes:
    """
    用 tar.gz 作为 gzip 对比。
    gzip 本身更适合压缩单个数据流；
    对目录整体压缩时，常见做法是先 tar 打包，再 gzip 压缩。
    """
    buffer = io.BytesIO()
    all_files = collect_all_files(site_root)

    with tarfile.open(fileobj=buffer, mode="w:gz") as tf:
        for abs_path, rel_path in all_files:
            tf.add(abs_path, arcname=rel_path)

    return buffer.getvalue()


def decompress_tar_gzip_bytes(tar_gzip_blob: bytes) -> int:
    """
    解压 tar.gz 到内存，不落盘。返回解出的文件数量。
    """
    count = 0
    buffer = io.BytesIO(tar_gzip_blob)

    with tarfile.open(fileobj=buffer, mode="r:gz") as tf:
        for member in tf.getmembers():
            if member.isfile():
                f = tf.extractfile(member)
                if f is not None:
                    _ = f.read()
                    count += 1

    return count


def evaluate_general_tools(site_root: str) -> Dict[str, float]:
    """
    评估 ZIP 和 tar.gz 的压缩大小、压缩耗时、解压耗时。
    """
    result = {}

    # ZIP
    zip_start = time.perf_counter()
    zip_blob = build_zip_bytes(site_root)
    zip_compress_ms = (time.perf_counter() - zip_start) * 1000

    zip_restore_start = time.perf_counter()
    zip_file_count = decompress_zip_bytes(zip_blob)
    zip_decompress_ms = (time.perf_counter() - zip_restore_start) * 1000

    result["zip_size"] = len(zip_blob)
    result["zip_compress_ms"] = zip_compress_ms
    result["zip_decompress_ms"] = zip_decompress_ms
    result["zip_file_count"] = zip_file_count

    # tar.gz
    gzip_start = time.perf_counter()
    gzip_blob = build_tar_gzip_bytes(site_root)
    gzip_compress_ms = (time.perf_counter() - gzip_start) * 1000

    gzip_restore_start = time.perf_counter()
    gzip_file_count = decompress_tar_gzip_bytes(gzip_blob)
    gzip_decompress_ms = (time.perf_counter() - gzip_restore_start) * 1000

    result["tar_gzip_size"] = len(gzip_blob)
    result["tar_gzip_compress_ms"] = gzip_compress_ms
    result["tar_gzip_decompress_ms"] = gzip_decompress_ms
    result["tar_gzip_file_count"] = gzip_file_count

    return result


def evaluate_our_system(site_root: str) -> Tuple[Dict, List[Dict]]:
    """
    评估当前自研系统：
    - 文本：整站 bundle_pre_lz77_huffman_text
    - 图片：jpeg_quality / png_optimize / store_original_image
    """
    resource_manager = ResourceManager()
    image_compressor = ImageCompressor()
    text_bundle_compressor = TextBundleCompressor()

    project = resource_manager.scan_project(site_root)
    resources = project.resources

    text_resources = [r for r in resources if r.resource_type == "text"]
    image_resources = [r for r in resources if r.resource_type == "image"]
    unsupported_resources = [r for r in resources if r.resource_type == "unsupported"]

    original_total = sum(r.original_size for r in resources)

    text_original_size = 0
    text_bundle_size = 0
    text_compress_ms = 0.0
    text_decompress_ms = 0.0
    text_restore_ok = True

    file_detail_rows = []

    # ----------------------------
    # 1) 文本 bundle 压缩
    # ----------------------------
    if text_resources:
        files = []
        for resource in text_resources:
            raw = read_binary(resource.file_path)
            rel_path = resource.relative_path.replace("\\", "/")
            files.append((rel_path, raw))
            text_original_size += len(raw)

        text_start = time.perf_counter()
        bundle_blob = text_bundle_compressor.compress_files(files)
        text_compress_ms = (time.perf_counter() - text_start) * 1000

        text_bundle_size = len(bundle_blob)

        restore_start = time.perf_counter()
        restored_map = text_bundle_compressor.decompress_files(bundle_blob)
        text_decompress_ms = (time.perf_counter() - restore_start) * 1000

        for rel_path, raw in files:
            restored = restored_map.get(rel_path)
            if restored != raw:
                text_restore_ok = False

        # 单文件明细中，bundle 不能严格拆分到每个文件。
        # 这里用“按原始大小比例分摊”的估算值，方便做热力图/明细图。
        for resource in text_resources:
            if text_original_size > 0:
                estimated_size = int(resource.original_size / text_original_size * text_bundle_size)
                estimated_compress_ms = resource.original_size / text_original_size * text_compress_ms
                estimated_decompress_ms = resource.original_size / text_original_size * text_decompress_ms
            else:
                estimated_size = 0
                estimated_compress_ms = 0.0
                estimated_decompress_ms = 0.0

            file_detail_rows.append({
                "sample_name": os.path.basename(site_root),
                "relative_path": resource.relative_path.replace("\\", "/"),
                "resource_type": "text",
                "original_size": resource.original_size,
                "compressed_size": estimated_size,
                "compression_rate": f"{calc_rate(resource.original_size, estimated_size):.2f}",
                "compress_time_ms": f"{estimated_compress_ms:.3f}",
                "decompress_time_ms": f"{estimated_decompress_ms:.3f}",
                "strategy": "bundle_pre_lz77_huffman_text",
                "note": "文本 bundle 的大小和耗时按原始大小比例估算到单文件"
            })

    # ----------------------------
    # 2) 图片逐文件压缩
    # ----------------------------
    image_original_size = 0
    image_compressed_size = 0
    image_compress_ms = 0.0

    for resource in image_resources:
        original_data = read_binary(resource.file_path)
        image_original_size += len(original_data)

        start = time.perf_counter()
        compressed_data, image_strategy = image_compressor.compress(resource.file_path, quality=70)
        elapsed_ms = (time.perf_counter() - start) * 1000
        image_compress_ms += elapsed_ms

        if len(compressed_data) >= len(original_data):
            final_data = original_data
            strategy = "store_original_image"
        else:
            final_data = compressed_data
            strategy = image_strategy

        image_compressed_size += len(final_data)

        file_detail_rows.append({
            "sample_name": os.path.basename(site_root),
            "relative_path": resource.relative_path.replace("\\", "/"),
            "resource_type": "image",
            "original_size": len(original_data),
            "compressed_size": len(final_data),
            "compression_rate": f"{calc_rate(len(original_data), len(final_data)):.2f}",
            "compress_time_ms": f"{elapsed_ms:.3f}",
            "decompress_time_ms": "0.000",
            "strategy": strategy,
            "note": "图片为可控质量压缩，恢复后保证可渲染"
        })

    # ----------------------------
    # 3) unsupported 资源保留原始大小
    # ----------------------------
    unsupported_original_size = 0
    for resource in unsupported_resources:
        unsupported_original_size += resource.original_size

        file_detail_rows.append({
            "sample_name": os.path.basename(site_root),
            "relative_path": resource.relative_path.replace("\\", "/"),
            "resource_type": "unsupported",
            "original_size": resource.original_size,
            "compressed_size": resource.original_size,
            "compression_rate": "0.00",
            "compress_time_ms": "0.000",
            "decompress_time_ms": "0.000",
            "strategy": "store_original_asset",
            "note": "不支持资源原样保存，用于保证恢复网页完整性"
        })

    compressed_total = text_bundle_size + image_compressed_size + unsupported_original_size
    compress_ms = text_compress_ms + image_compress_ms
    decompress_ms = text_decompress_ms

    summary = {
        "sample_name": os.path.basename(site_root),
        "site_root": site_root,
        "text_file_count": len(text_resources),
        "image_file_count": len(image_resources),
        "unsupported_file_count": len(unsupported_resources),

        "original_total_size": original_total,
        "system_compressed_total_size": compressed_total,
        "system_total_compression_rate": f"{calc_rate(original_total, compressed_total):.2f}",

        "text_original_size": text_original_size,
        "text_compressed_size": text_bundle_size,
        "text_compression_rate": f"{calc_rate(text_original_size, text_bundle_size):.2f}",

        "image_original_size": image_original_size,
        "image_compressed_size": image_compressed_size,
        "image_compression_rate": f"{calc_rate(image_original_size, image_compressed_size):.2f}",

        "system_compress_ms": f"{compress_ms:.3f}",
        "system_decompress_ms": f"{decompress_ms:.3f}",
        "text_restore_ok": "通过" if text_restore_ok else "失败",
        "render_check": "可通过恢复目录 index.html 人工打开验证"
    }

    return summary, file_detail_rows


def append_general_tool_results(summary: Dict, tool_result: Dict):
    original_size = int(summary["original_total_size"])

    zip_size = int(tool_result["zip_size"])
    gzip_size = int(tool_result["tar_gzip_size"])

    summary["zip_size"] = zip_size
    summary["zip_compression_rate"] = f"{calc_rate(original_size, zip_size):.2f}"
    summary["zip_compress_ms"] = f"{tool_result['zip_compress_ms']:.3f}"
    summary["zip_decompress_ms"] = f"{tool_result['zip_decompress_ms']:.3f}"

    summary["tar_gzip_size"] = gzip_size
    summary["tar_gzip_compression_rate"] = f"{calc_rate(original_size, gzip_size):.2f}"
    summary["tar_gzip_compress_ms"] = f"{tool_result['tar_gzip_compress_ms']:.3f}"
    summary["tar_gzip_decompress_ms"] = f"{tool_result['tar_gzip_decompress_ms']:.3f}"


def build_transmission_rows(summary_rows: List[Dict]) -> List[Dict]:
    rows = []

    for summary in summary_rows:
        sample_name = summary["sample_name"]

        original_size = int(summary["original_total_size"])
        system_size = int(summary["system_compressed_total_size"])
        zip_size = int(summary["zip_size"])
        gzip_size = int(summary["tar_gzip_size"])

        for network_name, bandwidth in NETWORK_PROFILES.items():
            original_sec = bytes_to_transfer_seconds(original_size, bandwidth)
            system_sec = bytes_to_transfer_seconds(system_size, bandwidth)
            zip_sec = bytes_to_transfer_seconds(zip_size, bandwidth)
            gzip_sec = bytes_to_transfer_seconds(gzip_size, bandwidth)

            rows.append({
                "sample_name": sample_name,
                "network": network_name,
                "bandwidth_mbps": bandwidth,

                "original_transfer_s": f"{original_sec:.6f}",
                "system_transfer_s": f"{system_sec:.6f}",
                "zip_transfer_s": f"{zip_sec:.6f}",
                "tar_gzip_transfer_s": f"{gzip_sec:.6f}",

                "system_saved_s": f"{original_sec - system_sec:.6f}",
                "system_improvement_rate": f"{calc_rate(original_size, system_size):.2f}"
            })

    return rows


def write_csv(path: str, rows: List[Dict]):
    ensure_dir(os.path.dirname(path))

    if not rows:
        return

    fieldnames = list(rows[0].keys())

    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    reports_dir = os.path.join(PROJECT_ROOT, "output", "reports")
    ensure_dir(reports_dir)

    summary_rows = []
    detail_rows = []

    print("=" * 70)
    print("开始评估网页压缩系统")
    print("=" * 70)

    for site_root in SAMPLE_SITES:
        if not os.path.exists(site_root):
            print(f"[跳过] 样本不存在: {site_root}")
            continue

        sample_name = os.path.basename(site_root)
        print(f"\n[样本] {sample_name}")
        print("-" * 70)

        print("[1/3] 评估自研压缩系统...")
        summary, details = evaluate_our_system(site_root)

        print("[2/3] 评估 ZIP / tar.gz 对比工具...")
        tool_result = evaluate_general_tools(site_root)
        append_general_tool_results(summary, tool_result)

        print("[3/3] 汇总结果...")
        summary_rows.append(summary)
        detail_rows.extend(details)

        print(f"文本文件数: {summary['text_file_count']}")
        print(f"图片文件数: {summary['image_file_count']}")
        print(f"原始总大小: {summary['original_total_size']} B")
        print(f"自研系统压缩后: {summary['system_compressed_total_size']} B")
        print(f"自研系统压缩率: {summary['system_total_compression_rate']}%")
        print(f"ZIP 压缩率: {summary['zip_compression_rate']}%")
        print(f"tar.gz 压缩率: {summary['tar_gzip_compression_rate']}%")
        print(f"文本恢复校验: {summary['text_restore_ok']}")

    transmission_rows = build_transmission_rows(summary_rows)

    summary_path = os.path.join(reports_dir, "experiment_summary.csv")
    detail_path = os.path.join(reports_dir, "file_detail.csv")
    transmission_path = os.path.join(reports_dir, "transmission_report.csv")

    write_csv(summary_path, summary_rows)
    write_csv(detail_path, detail_rows)
    write_csv(transmission_path, transmission_rows)

    print("\n" + "=" * 70)
    print("评估完成，已生成报告文件：")
    print(summary_path)
    print(detail_path)
    print(transmission_path)
    print("=" * 70)


if __name__ == "__main__":
    main()
