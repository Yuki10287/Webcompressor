import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.incremental_manager import IncrementalManager


def print_file_group(title: str, paths):
    print(f"\n{title} ({len(paths)})")
    print("-" * 60)
    if not paths:
        print("  无")
        return

    for path in paths:
        print(f"  {path}")


def main():
    site_root = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.path.join(PROJECT_ROOT, "sample_data", "benchmark_site_rich")
    )

    if not os.path.isabs(site_root):
        site_root = os.path.join(PROJECT_ROOT, site_root)

    manager = IncrementalManager()
    current_state = manager.scan_site(site_root)
    old_state = manager.load_state(site_root)
    result = manager.compare_states(old_state, current_state)
    manager.save_state(site_root, current_state)

    print("=" * 70)
    print("网页资源增量压缩检测实验")
    print("=" * 70)
    print(f"站点路径: {os.path.abspath(site_root)}")
    print(f"缓存文件: {manager.get_cache_path(site_root)}")
    print(f"当前文件总数: {len(current_state)}")
    print("-" * 70)
    print(f"新增文件数量: {len(result['new_files'])}")
    print(f"修改文件数量: {len(result['modified_files'])}")
    print(f"未变化文件数量: {len(result['unchanged_files'])}")
    print(f"删除文件数量: {len(result['deleted_files'])}")

    print_file_group("新增文件 new_files", result["new_files"])
    print_file_group("修改文件 modified_files", result["modified_files"])
    print_file_group("未变化文件 unchanged_files", result["unchanged_files"])
    print_file_group("删除文件 deleted_files", result["deleted_files"])

    print("\n检测完成，已更新增量缓存。")
    print("=" * 70)


if __name__ == "__main__":
    main()
