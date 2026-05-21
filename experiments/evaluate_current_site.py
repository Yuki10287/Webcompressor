import csv
import json
import os
import sys
from typing import Dict, List, Optional

import matplotlib.pyplot as plt


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from experiments.evaluate_system import (
    append_general_tool_results,
    build_transmission_rows,
    evaluate_general_tools,
    evaluate_our_system,
)
from utils.file_utils import ensure_dir


SITES_REPORT_ROOT = os.path.join(PROJECT_ROOT, "output", "reports", "sites")
RECENT_SITE_PATH = os.path.join(PROJECT_ROOT, "output", "reports", "recent_site_path.txt")

BLUE_GRAY_MAIN = "#7E93A8"
BLUE_GRAY_DARK = "#5F7489"
BLUE_GRAY_LIGHT = "#B7C6D8"
DUSTY_PINK_MAIN = "#D8A7B1"
DUSTY_PINK_DARK = "#B98592"
DUSTY_PINK_LIGHT = "#EED6DB"
BG_LIGHT = "#F5F6F8"
BORDER_GRAY = "#D9DDE3"
TEXT_DARK = "#4A5563"
WHITE = "#FFFFFF"
CHART_DPI = 200

SOFT_PALETTE = [
    BLUE_GRAY_MAIN,
    DUSTY_PINK_MAIN,
    BLUE_GRAY_LIGHT,
    DUSTY_PINK_LIGHT,
    BLUE_GRAY_DARK,
    DUSTY_PINK_DARK,
]


def calc_rate(original_size: int, compressed_size: int) -> float:
    if original_size <= 0:
        return 0.0
    return (original_size - compressed_size) / original_size * 100.0


def to_float(value) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def to_int(value) -> int:
    try:
        return int(float(value))
    except Exception:
        return 0


def safe_site_name(site_root: str) -> str:
    name = os.path.basename(os.path.abspath(site_root))
    return "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in name) or "site"


def get_site_report_dir(site_root: str) -> str:
    return os.path.join(SITES_REPORT_ROOT, safe_site_name(site_root))


def get_site_chart_dir(site_root: str) -> str:
    return os.path.join(get_site_report_dir(site_root), "charts")


def record_recent_site_path(site_root: str) -> None:
    ensure_dir(os.path.dirname(RECENT_SITE_PATH))
    with open(RECENT_SITE_PATH, "w", encoding="utf-8") as f:
        f.write(os.path.abspath(site_root))


def read_recent_site_path() -> Optional[str]:
    candidates = [RECENT_SITE_PATH]

    manifest_path = os.path.join(PROJECT_ROOT, "output", "compressed", "manifest.json")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                project_root = json.load(f).get("project_root", "")
            if project_root:
                candidates.append(project_root)
        except Exception:
            pass

    for candidate in candidates:
        if not candidate:
            continue
        if candidate == RECENT_SITE_PATH:
            if not os.path.exists(candidate):
                continue
            with open(candidate, "r", encoding="utf-8") as f:
                path = f.read().strip()
        else:
            path = candidate

        if path and os.path.isdir(path):
            return os.path.abspath(path)

    return None


def write_csv(path: str, rows: List[Dict]) -> None:
    ensure_dir(os.path.dirname(path))
    if not rows:
        return

    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def setup_font() -> None:
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.facecolor"] = BG_LIGHT
    plt.rcParams["axes.facecolor"] = WHITE
    plt.rcParams["axes.edgecolor"] = BORDER_GRAY
    plt.rcParams["axes.labelcolor"] = TEXT_DARK
    plt.rcParams["axes.titlecolor"] = TEXT_DARK
    plt.rcParams["xtick.color"] = TEXT_DARK
    plt.rcParams["ytick.color"] = TEXT_DARK
    plt.rcParams["legend.frameon"] = True
    plt.rcParams["legend.facecolor"] = WHITE
    plt.rcParams["legend.edgecolor"] = BORDER_GRAY
    plt.rcParams["text.color"] = TEXT_DARK


def make_figure(figsize):
    fig, ax = plt.subplots(figsize=figsize, facecolor=BG_LIGHT)
    ax.set_facecolor(WHITE)
    return fig, ax


def apply_axis_style(ax, grid_axis: str = "y") -> None:
    ax.grid(axis=grid_axis, color=BORDER_GRAY, alpha=0.55, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(BORDER_GRAY)


def apply_legend_style(ax) -> None:
    legend = ax.legend()
    if legend is None:
        return
    legend.get_frame().set_facecolor(WHITE)
    legend.get_frame().set_edgecolor(BORDER_GRAY)
    legend.get_frame().set_alpha(0.92)


def save_chart(fig, path: str) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=CHART_DPI, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def save_total_compression_compare(summary: Dict, chart_dir: str) -> None:
    labels = ["Original", "Our System", "ZIP", "tar.gz"]
    sizes = [
        to_int(summary["original_total_size"]),
        to_int(summary["system_compressed_total_size"]),
        to_int(summary["zip_size"]),
        to_int(summary["tar_gzip_size"]),
    ]

    fig, ax = make_figure((9, 5.6))
    bars = ax.bar(labels, sizes, color=[BLUE_GRAY_DARK, BLUE_GRAY_MAIN, DUSTY_PINK_MAIN, BLUE_GRAY_LIGHT],
                  edgecolor=WHITE, linewidth=0.9)
    ax.set_ylabel("Size / bytes")
    ax.set_title(f"{summary['sample_name']} total compression comparison", pad=14)
    apply_axis_style(ax)

    for bar, size in zip(bars, sizes):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), str(size),
                ha="center", va="bottom", color=TEXT_DARK, fontsize=9)

    save_chart(fig, os.path.join(chart_dir, "total_compression_compare.png"))


def save_resource_type_pie(summary: Dict, chart_dir: str) -> None:
    text_size = to_int(summary["text_original_size"])
    image_size = to_int(summary["image_original_size"])
    unsupported_size = to_int(summary["original_total_size"]) - text_size - image_size

    labels = []
    sizes = []
    if text_size > 0:
        labels.append("Text")
        sizes.append(text_size)
    if image_size > 0:
        labels.append("Image")
        sizes.append(image_size)
    if unsupported_size > 0:
        labels.append("Unsupported")
        sizes.append(unsupported_size)

    if not sizes:
        labels = ["Empty"]
        sizes = [1]

    fig, ax = make_figure((7, 7))
    ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90,
        colors=SOFT_PALETTE[:len(sizes)],
        wedgeprops={"edgecolor": WHITE, "linewidth": 1.2},
        textprops={"color": TEXT_DARK, "fontsize": 10},
    )
    ax.set_title(f"{summary['sample_name']} resource type share", pad=14)
    ax.axis("equal")
    save_chart(fig, os.path.join(chart_dir, "resource_type_pie.png"))


def save_file_compression_heatmap(detail_rows: List[Dict], chart_dir: str) -> None:
    rows = [r for r in detail_rows if r.get("resource_type") != "unsupported"]
    rows = sorted(rows, key=lambda r: to_float(r.get("compression_rate")), reverse=True)

    if not rows:
        rows = [{
            "relative_path": "No compressible files",
            "compression_rate": "0",
        }]

    names = [r["relative_path"] for r in rows]
    rates = [to_float(r["compression_rate"]) for r in rows]
    height = max(5.5, min(18, len(rows) * 0.35))

    fig, ax = make_figure((11, height))
    colors = [SOFT_PALETTE[i % len(SOFT_PALETTE)] for i in range(len(rates))]
    ax.barh(names, rates, color=colors, edgecolor=WHITE, linewidth=0.7)
    ax.set_xlabel("Compression rate / %")
    ax.set_title("File compression heatmap", pad=14)
    ax.invert_yaxis()
    apply_axis_style(ax, grid_axis="x")
    save_chart(fig, os.path.join(chart_dir, "file_compression_heatmap.png"))


def save_transmission_compare(transmission_rows: List[Dict], chart_dir: str) -> None:
    networks = [r["network"] for r in transmission_rows]
    original_times = [to_float(r["original_transfer_s"]) for r in transmission_rows]
    system_times = [to_float(r["system_transfer_s"]) for r in transmission_rows]
    zip_times = [to_float(r["zip_transfer_s"]) for r in transmission_rows]
    gzip_times = [to_float(r["tar_gzip_transfer_s"]) for r in transmission_rows]

    x = range(len(networks))
    width = 0.2

    fig, ax = make_figure((10, 5.8))
    ax.bar([i - 1.5 * width for i in x], original_times, width, label="Original",
           color=BLUE_GRAY_DARK, edgecolor=WHITE, linewidth=0.8)
    ax.bar([i - 0.5 * width for i in x], system_times, width, label="Our System",
           color=BLUE_GRAY_MAIN, edgecolor=WHITE, linewidth=0.8)
    ax.bar([i + 0.5 * width for i in x], zip_times, width, label="ZIP",
           color=DUSTY_PINK_MAIN, edgecolor=WHITE, linewidth=0.8)
    ax.bar([i + 1.5 * width for i in x], gzip_times, width, label="tar.gz",
           color=BLUE_GRAY_LIGHT, edgecolor=WHITE, linewidth=0.8)

    ax.set_xticks(list(x), networks)
    ax.set_ylabel("Transfer time / seconds")
    ax.set_title("Transmission time comparison", pad=14)
    apply_axis_style(ax)
    apply_legend_style(ax)
    save_chart(fig, os.path.join(chart_dir, "transmission_compare.png"))


def generate_site_charts(summary: Dict, detail_rows: List[Dict], transmission_rows: List[Dict], chart_dir: str) -> None:
    """基于当前站点的一组 CSV 数据生成四张可视化图表。"""
    setup_font()
    ensure_dir(chart_dir)
    save_total_compression_compare(summary, chart_dir)
    save_resource_type_pie(summary, chart_dir)
    save_file_compression_heatmap(detail_rows, chart_dir)
    save_transmission_compare(transmission_rows, chart_dir)


def evaluate_current_site(site_root: str) -> Dict[str, str]:
    """
    对用户当前选择的网页目录生成单站点评估报告。

    注意：这里会重新执行一轮压缩评估，并额外生成 ZIP / tar.gz 对比结果。
    它用于报告展示，不会复用 GUI 压缩按钮已经产生的 manifest。
    """
    site_root = os.path.abspath(site_root)
    if not os.path.isdir(site_root):
        raise FileNotFoundError(f"Site directory not found: {site_root}")

    report_dir = get_site_report_dir(site_root)
    chart_dir = os.path.join(report_dir, "charts")
    ensure_dir(report_dir)

    # 自研系统结果用于展示压缩率和文件明细，通用工具结果用于横向对比。
    summary, detail_rows = evaluate_our_system(site_root)
    tool_result = evaluate_general_tools(site_root)
    append_general_tool_results(summary, tool_result)

    summary_rows = [summary]
    transmission_rows = build_transmission_rows(summary_rows)

    summary_path = os.path.join(report_dir, "summary.csv")
    detail_path = os.path.join(report_dir, "file_detail.csv")
    transmission_path = os.path.join(report_dir, "transmission_report.csv")

    write_csv(summary_path, summary_rows)
    write_csv(detail_path, detail_rows)
    write_csv(transmission_path, transmission_rows)
    # 图表和 CSV 放在同一个站点报告目录下，便于 GUI 直接打开查看。
    generate_site_charts(summary, detail_rows, transmission_rows, chart_dir)
    record_recent_site_path(site_root)

    return {
        "site_root": site_root,
        "site_name": summary["sample_name"],
        "report_dir": report_dir,
        "chart_dir": chart_dir,
        "summary_csv": summary_path,
        "file_detail_csv": detail_path,
        "transmission_csv": transmission_path,
    }


def main() -> int:
    if len(sys.argv) > 1:
        site_root = sys.argv[1]
    else:
        site_root = read_recent_site_path()
        if not site_root:
            print("Please pass a site directory path, for example:")
            print("python experiments/evaluate_current_site.py sample_data/real_site_pythonTutorial")
            return 1

    result = evaluate_current_site(site_root)
    print("Current site report generated:")
    print(result["report_dir"])
    print(result["chart_dir"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
