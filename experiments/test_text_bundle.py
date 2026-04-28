import os
import sys
import time

from core.resource_manager import ResourceManager
from compress.text_compressor import TextCompressor
from compress.text_bundle_compressor import TextBundleCompressor
from utils.file_utils import ensure_dir, read_binary, write_binary


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def calc_rate(original_size: int, compressed_size: int) -> float:
    if original_size == 0:
        return 0.0
    return (original_size - compressed_size) / original_size * 100.0


def main():
    site_root = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.path.join(PROJECT_ROOT, "sample_data", "benchmark_site_rich")
    )

    if not os.path.isabs(site_root):
        site_root = os.path.join(PROJECT_ROOT, site_root)

    resource_manager = ResourceManager()
    project = resource_manager.scan_project(site_root)

    text_resources = [r for r in project.resources if r.resource_type == "text"]

    if not text_resources:
        print(f"没有找到文本资源。当前路径：{site_root}")
        return

    files = []
    total_text_original = 0

    # 统一把相对路径规范成 / ，避免 Windows 下 \ 和 / 导致校验误判
    for resource in text_resources:
        raw = read_binary(resource.file_path)
        normalized_path = resource.relative_path.replace("\\", "/")
        files.append((normalized_path, raw))
        total_text_original += len(raw)

    print("=" * 60)
    print(f"站点: {site_root}")
    print(f"文本文件数量: {len(text_resources)}")
    print(f"文本原始总大小: {total_text_original} B")

    # -------------------------------------------------
    # 1) 当前逐文件压缩版（作为对照）
    # -------------------------------------------------
    print("[1/4] 开始计算逐文件文本压缩结果...")
    single_compressor = TextCompressor()
    single_total = 0

    single_start = time.perf_counter()
    for relative_path, raw in files:
        compressed = single_compressor.compress(raw, relative_path)

        # 保持和 GUI 一致：若压缩后不划算，则回退保留原文
        if len(compressed) >= len(raw):
            single_total += len(raw)
        else:
            single_total += len(compressed)

    single_compress_ms = (time.perf_counter() - single_start) * 1000

    # -------------------------------------------------
    # 2) 整站 bundle 压缩版
    # -------------------------------------------------
    print("[2/4] 开始整站 bundle 压缩...")
    bundle_compressor = TextBundleCompressor()

    bundle_start = time.perf_counter()
    bundle_blob = bundle_compressor.compress_files(files)
    bundle_compress_ms = (time.perf_counter() - bundle_start) * 1000

    # -------------------------------------------------
    # 3) 解压并校验
    # -------------------------------------------------
    print("[3/4] 开始 bundle 解压与恢复校验...")
    bundle_restore_start = time.perf_counter()
    restored_map = bundle_compressor.decompress_files(bundle_blob)
    bundle_restore_ms = (time.perf_counter() - bundle_restore_start) * 1000

    all_ok = True
    for relative_path, raw in files:
        restored = restored_map.get(relative_path)

        if restored is None:
            print(f"[校验失败: 路径缺失] {relative_path}")
            all_ok = False
        elif restored != raw:
            print(f"[校验失败: 内容不一致] {relative_path}")
            all_ok = False

    # -------------------------------------------------
    # 4) 输出统计
    # -------------------------------------------------
    print("[4/4] 开始输出统计结果...")
    print("-" * 60)
    print("逐文件 pre_lz77_huffman_text")
    print(f"文本压缩后总大小: {single_total} B")
    print(f"文本压缩率: {calc_rate(total_text_original, single_total):.2f}%")
    print(f"压缩耗时: {single_compress_ms:.3f} ms")

    print("-" * 60)
    print("整站 bundle_pre_lz77_huffman_text")
    print(f"文本压缩后总大小: {len(bundle_blob)} B")
    print(f"文本压缩率: {calc_rate(total_text_original, len(bundle_blob)):.2f}%")
    print(f"压缩耗时: {bundle_compress_ms:.3f} ms")
    print(f"解压耗时: {bundle_restore_ms:.3f} ms")
    print(f"恢复校验: {'通过' if all_ok else '失败'}")

    # -------------------------------------------------
    # 输出文件
    # -------------------------------------------------
    site_name = os.path.basename(os.path.abspath(site_root))
    bundle_output_dir = os.path.join(PROJECT_ROOT, "output", "bundles")
    restored_output_dir = os.path.join(PROJECT_ROOT, "output", "restored_bundle_text", site_name)

    ensure_dir(bundle_output_dir)
    ensure_dir(restored_output_dir)

    bundle_path = os.path.join(bundle_output_dir, f"{site_name}_text_bundle.bin")
    write_binary(bundle_path, bundle_blob)

    for relative_path, raw in restored_map.items():
        target_path = os.path.join(restored_output_dir, relative_path)
        write_binary(target_path, raw)

    print("-" * 60)
    print(f"bundle 文件输出: {bundle_path}")
    print(f"恢复文本输出: {restored_output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()