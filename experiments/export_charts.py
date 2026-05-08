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


def save_total_compression_rate(summary_rows):
    samples = [r["sample_name"] for r in summary_rows]
    system_rates = [to_float(r["system_total_compression_rate"]) for r in summary_rows]
    zip_rates = [to_float(r["zip_compression_rate"]) for r in summary_rows]
    gzip_rates = [to_float(r["tar_gzip_compression_rate"]) for r in summary_rows]

    x = range(len(samples))
    width = 0.25

    plt.figure(figsize=(10, 6))
    plt.bar([i - width for i in x], system_rates, width, label="自研系统")
    plt.bar(x, zip_rates, width, label="ZIP")
    plt.bar([i + width for i in x], gzip_rates, width, label="tar.gz")

    plt.xticks(list(x), samples)
    plt.ylabel("压缩率 / %")
    plt.title("不同样本下的总体压缩率对比")
    plt.legend()
    plt.tight_layout()

    path = os.path.join(CHART_DIR, "total_compression_rate.png")
    plt.savefig(path, dpi=180)
    plt.close()
    print(f"已生成: {path}")


def save_text_image_compression_rate(summary_rows):
    samples = [r["sample_name"] for r in summary_rows]
    text_rates = [to_float(r["text_compression_rate"]) for r in summary_rows]
    image_rates = [to_float(r["image_compression_rate"]) for r in summary_rows]

    x = range(len(samples))
    width = 0.35

    plt.figure(figsize=(10, 6))
    plt.bar([i - width / 2 for i in x], text_rates, width, label="文本资源")
    plt.bar([i + width / 2 for i in x], image_rates, width, label="图片资源")

    plt.xticks(list(x), samples)
    plt.ylabel("压缩率 / %")
    plt.title("文本资源与图片资源压缩率对比")
    plt.legend()
    plt.tight_layout()

    path = os.path.join(CHART_DIR, "text_image_compression_rate.png")
    plt.savefig(path, dpi=180)
    plt.close()
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

        plt.figure(figsize=(7, 7))
        plt.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
        plt.title(f"{sample} 原始资源类型占比")
        plt.tight_layout()

        path = os.path.join(CHART_DIR, f"{sample}_resource_type_pie.png")
        plt.savefig(path, dpi=180)
        plt.close()
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

        plt.figure(figsize=(12, height))
        plt.barh(names, rates)
        plt.xlabel("压缩率 / %")
        plt.title(f"{sample} 单文件压缩率热力图/排序图")
        plt.gca().invert_yaxis()
        plt.tight_layout()

        path = os.path.join(CHART_DIR, f"{sample}_file_compression_heatmap.png")
        plt.savefig(path, dpi=180)
        plt.close()
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

        plt.figure(figsize=(10, 6))
        plt.bar([i - 1.5 * width for i in x], original_times, width, label="原始资源")
        plt.bar([i - 0.5 * width for i in x], system_times, width, label="自研系统")
        plt.bar([i + 0.5 * width for i in x], zip_times, width, label="ZIP")
        plt.bar([i + 1.5 * width for i in x], gzip_times, width, label="tar.gz")

        plt.xticks(list(x), networks)
        plt.ylabel("传输时间 / 秒")
        plt.title(f"{sample} 不同网络环境下传输时间对比")
        plt.legend()
        plt.tight_layout()

        path = os.path.join(CHART_DIR, f"{sample}_transmission_compare.png")
        plt.savefig(path, dpi=180)
        plt.close()
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

    if transmission_rows:
        save_transmission_compare(transmission_rows)

    print("图表导出完成。")


if __name__ == "__main__":
    main()