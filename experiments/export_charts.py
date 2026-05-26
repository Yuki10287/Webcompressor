import csv
import os
import sys
from collections import defaultdict

import matplotlib.pyplot as plt


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_DIR = os.path.join(PROJECT_ROOT, "output", "reports")
CHART_DIR = os.path.join(REPORT_DIR, "charts")

SUMMARY_CSV = os.path.join(REPORT_DIR, "experiment_summary.csv")
DETAIL_CSV = os.path.join(REPORT_DIR, "file_detail.csv")
TRANSMISSION_CSV = os.path.join(REPORT_DIR, "transmission_report.csv")

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

SERIES_COLORS = {
    "自研系统": BLUE_GRAY_MAIN,
    "ZIP": DUSTY_PINK_MAIN,
    "tar.gz": BLUE_GRAY_LIGHT,
    "原始资源": BLUE_GRAY_DARK,
    "文本资源": BLUE_GRAY_MAIN,
    "图片资源": DUSTY_PINK_MAIN,
    "其他资源": DUSTY_PINK_LIGHT,
}

SOFT_PALETTE = [
    BLUE_GRAY_MAIN,
    DUSTY_PINK_MAIN,
    BLUE_GRAY_LIGHT,
    BLUE_GRAY_DARK,
    DUSTY_PINK_LIGHT,
    DUSTY_PINK_DARK,
]


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def read_csv(path: str):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def to_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0


def to_int(value):
    try:
        return int(float(value))
    except Exception:
        return 0


def setup_font():
    # Windows 下优先使用微软雅黑，避免中文乱码
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.facecolor"] = BG_LIGHT
    plt.rcParams["axes.facecolor"] = WHITE
    plt.rcParams["axes.edgecolor"] = BORDER_GRAY
    plt.rcParams["axes.labelcolor"] = TEXT_DARK
    plt.rcParams["axes.titlecolor"] = TEXT_DARK
    plt.rcParams["axes.titlesize"] = 15
    plt.rcParams["axes.titleweight"] = "semibold"
    plt.rcParams["axes.labelsize"] = 11
    plt.rcParams["xtick.color"] = TEXT_DARK
    plt.rcParams["ytick.color"] = TEXT_DARK
    plt.rcParams["legend.frameon"] = True
    plt.rcParams["legend.facecolor"] = WHITE
    plt.rcParams["legend.edgecolor"] = BORDER_GRAY
    plt.rcParams["legend.fontsize"] = 10
    plt.rcParams["text.color"] = TEXT_DARK


def make_figure(figsize):
    fig, ax = plt.subplots(figsize=figsize, facecolor=BG_LIGHT)
    ax.set_facecolor(WHITE)
    return fig, ax


def apply_axis_style(ax, grid_axis="y"):
    ax.tick_params(axis="both", colors=TEXT_DARK, labelsize=10)
    ax.title.set_color(TEXT_DARK)
    ax.xaxis.label.set_color(TEXT_DARK)
    ax.yaxis.label.set_color(TEXT_DARK)
    ax.grid(axis=grid_axis, color=BORDER_GRAY, alpha=0.55, linewidth=0.8)
    ax.set_axisbelow(True)

    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(BORDER_GRAY)
        ax.spines[side].set_linewidth(1.0)


def apply_legend_style(ax):
    legend = ax.legend()
    if legend is None:
        return

    legend.get_frame().set_facecolor(WHITE)
    legend.get_frame().set_edgecolor(BORDER_GRAY)
    legend.get_frame().set_alpha(0.92)
    for text in legend.get_texts():
        text.set_color(TEXT_DARK)


def color_sequence(count):
    return [SOFT_PALETTE[i % len(SOFT_PALETTE)] for i in range(count)]


def save_chart(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=CHART_DPI, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def save_total_compression_rate(summary_rows):
    samples = [r["sample_name"] for r in summary_rows]
    system_rates = [to_float(r["system_total_compression_rate"]) for r in summary_rows]
    zip_rates = [to_float(r["zip_compression_rate"]) for r in summary_rows]
    gzip_rates = [to_float(r["tar_gzip_compression_rate"]) for r in summary_rows]

    x = range(len(samples))
    width = 0.25

    fig, ax = make_figure(figsize=(10, 6))
    ax.bar(
        [i - width for i in x], system_rates, width,
        label="自研系统", color=SERIES_COLORS["自研系统"],
        edgecolor=WHITE, linewidth=0.8
    )
    ax.bar(
        x, zip_rates, width,
        label="ZIP", color=SERIES_COLORS["ZIP"],
        edgecolor=WHITE, linewidth=0.8
    )
    ax.bar(
        [i + width for i in x], gzip_rates, width,
        label="tar.gz", color=SERIES_COLORS["tar.gz"],
        edgecolor=WHITE, linewidth=0.8
    )

    ax.set_xticks(list(x), samples)
    ax.set_ylabel("压缩率 / %")
    ax.set_title("不同样本下的总体压缩率对比", pad=14)
    apply_axis_style(ax)
    apply_legend_style(ax)

    path = os.path.join(CHART_DIR, "total_compression_rate.png")
    save_chart(fig, path)
    print(f"已生成: {path}")


def save_text_image_compression_rate(summary_rows):
    samples = [r["sample_name"] for r in summary_rows]
    text_rates = [to_float(r["text_compression_rate"]) for r in summary_rows]
    image_rates = [to_float(r["image_compression_rate"]) for r in summary_rows]

    x = range(len(samples))
    width = 0.35

    fig, ax = make_figure(figsize=(10, 6))
    ax.bar(
        [i - width / 2 for i in x], text_rates, width,
        label="文本资源", color=SERIES_COLORS["文本资源"],
        edgecolor=WHITE, linewidth=0.8
    )
    ax.bar(
        [i + width / 2 for i in x], image_rates, width,
        label="图片资源", color=SERIES_COLORS["图片资源"],
        edgecolor=WHITE, linewidth=0.8
    )

    ax.set_xticks(list(x), samples)
    ax.set_ylabel("压缩率 / %")
    ax.set_title("文本资源与图片资源压缩率对比", pad=14)
    apply_axis_style(ax)
    apply_legend_style(ax)

    path = os.path.join(CHART_DIR, "text_image_compression_rate.png")
    save_chart(fig, path)
    print(f"已生成: {path}")


def save_resource_type_pie(summary_rows):
    for row in summary_rows:
        sample = row["sample_name"]

        text_size = to_int(row["text_original_size"])
        image_size = to_int(row["image_original_size"])
        unsupported_size = (
            to_int(row["original_total_size"])
            - text_size
            - image_size
        )

        labels = []
        sizes = []

        if text_size > 0:
            labels.append("文本资源")
            sizes.append(text_size)
        if image_size > 0:
            labels.append("图片资源")
            sizes.append(image_size)
        if unsupported_size > 0:
            labels.append("其他资源")
            sizes.append(unsupported_size)

        fig, ax = make_figure(figsize=(7, 7))
        colors = [SERIES_COLORS.get(label, SOFT_PALETTE[i % len(SOFT_PALETTE)]) for i, label in enumerate(labels)]
        _wedges, _texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            colors=colors,
            wedgeprops={"edgecolor": WHITE, "linewidth": 1.2},
            textprops={"color": TEXT_DARK, "fontsize": 10},
        )
        for text in autotexts:
            text.set_color(TEXT_DARK)
            text.set_fontsize(10)
        ax.set_title(f"{sample} 原始资源类型占比", pad=14)
        ax.axis("equal")

        path = os.path.join(CHART_DIR, f"{sample}_resource_type_pie.png")
        save_chart(fig, path)
        print(f"已生成: {path}")


def save_file_compression_heatmap(detail_rows):
    by_sample = defaultdict(list)
    for row in detail_rows:
        if row["resource_type"] == "unsupported":
            continue
        by_sample[row["sample_name"]].append(row)

    for sample, rows in by_sample.items():
        rows = sorted(
            rows,
            key=lambda r: to_float(r["compression_rate"]),
            reverse=True
        )

        names = [r["relative_path"] for r in rows]
        rates = [to_float(r["compression_rate"]) for r in rows]

        # 文件太多时图会很长，所以动态调整高度
        height = max(6, len(rows) * 0.35)

        fig, ax = make_figure(figsize=(12, height))
        ax.barh(names, rates, color=color_sequence(len(rates)), edgecolor=WHITE, linewidth=0.7)
        ax.set_xlabel("压缩率 / %")
        ax.set_title(f"{sample} 单文件压缩率热力图/排序图", pad=14)
        ax.invert_yaxis()
        apply_axis_style(ax, grid_axis="x")

        path = os.path.join(CHART_DIR, f"{sample}_file_compression_heatmap.png")
        save_chart(fig, path)
        print(f"已生成: {path}")


def save_file_compress_time_chart(detail_rows):
    by_sample = defaultdict(list)
    for row in detail_rows:
        if row["resource_type"] == "unsupported":
            continue
        if to_float(row.get("compress_time_ms")) <= 0:
            continue
        by_sample[row["sample_name"]].append(row)

    for sample, rows in by_sample.items():
        rows = sorted(
            rows,
            key=lambda r: to_float(r.get("compress_time_ms")),
            reverse=True
        )

        names = [r["relative_path"] for r in rows]
        times = [to_float(r.get("compress_time_ms")) for r in rows]
        height = max(6, len(rows) * 0.35)

        fig, ax = make_figure(figsize=(12, height))
        ax.barh(names, times, color=color_sequence(len(times)), edgecolor=WHITE, linewidth=0.7)
        ax.set_xlabel("压缩耗时 / ms")
        ax.set_title(f"{sample} 单文件压缩耗时排序图", pad=14)
        ax.invert_yaxis()
        apply_axis_style(ax, grid_axis="x")

        path = os.path.join(CHART_DIR, f"{sample}_file_compress_time.png")
        save_chart(fig, path)
        print(f"已生成: {path}")


def save_transmission_compare(transmission_rows):
    by_sample = defaultdict(list)
    for row in transmission_rows:
        by_sample[row["sample_name"]].append(row)

    for sample, rows in by_sample.items():
        networks = [r["network"] for r in rows]
        original_times = [to_float(r["original_transfer_s"]) for r in rows]
        system_times = [to_float(r["system_transfer_s"]) for r in rows]
        zip_times = [to_float(r["zip_transfer_s"]) for r in rows]
        gzip_times = [to_float(r["tar_gzip_transfer_s"]) for r in rows]

        x = range(len(networks))
        width = 0.2

        fig, ax = make_figure(figsize=(10, 6))
        ax.bar(
            [i - 1.5 * width for i in x], original_times, width,
            label="原始资源", color=SERIES_COLORS["原始资源"],
            edgecolor=WHITE, linewidth=0.8
        )
        ax.bar(
            [i - 0.5 * width for i in x], system_times, width,
            label="自研系统", color=SERIES_COLORS["自研系统"],
            edgecolor=WHITE, linewidth=0.8
        )
        ax.bar(
            [i + 0.5 * width for i in x], zip_times, width,
            label="ZIP", color=SERIES_COLORS["ZIP"],
            edgecolor=WHITE, linewidth=0.8
        )
        ax.bar(
            [i + 1.5 * width for i in x], gzip_times, width,
            label="tar.gz", color=SERIES_COLORS["tar.gz"],
            edgecolor=WHITE, linewidth=0.8
        )

        ax.set_xticks(list(x), networks)
        ax.set_ylabel("传输时间 / 秒")
        ax.set_title(f"{sample} 不同网络环境下传输时间对比", pad=14)
        apply_axis_style(ax)
        apply_legend_style(ax)

        path = os.path.join(CHART_DIR, f"{sample}_transmission_compare.png")
        save_chart(fig, path)
        print(f"已生成: {path}")


def main():
    setup_font()
    ensure_dir(CHART_DIR)

    if not os.path.exists(SUMMARY_CSV):
        print("未找到 experiment_summary.csv，请先运行 experiments/evaluate_system.py")
        return

    summary_rows = read_csv(SUMMARY_CSV)
    detail_rows = read_csv(DETAIL_CSV) if os.path.exists(DETAIL_CSV) else []
    transmission_rows = read_csv(TRANSMISSION_CSV) if os.path.exists(TRANSMISSION_CSV) else []

    save_total_compression_rate(summary_rows)
    save_text_image_compression_rate(summary_rows)
    save_resource_type_pie(summary_rows)

    if detail_rows:
        save_file_compression_heatmap(detail_rows)
        save_file_compress_time_chart(detail_rows)

    if transmission_rows:
        save_transmission_compare(transmission_rows)

    print("图表导出完成。")


if __name__ == "__main__":
    main()
