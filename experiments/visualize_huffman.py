import csv
import heapq
import os
import sys
from collections import Counter
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

import matplotlib.pyplot as plt


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

REPORT_DIR = os.path.join(PROJECT_ROOT, "output", "reports")
CHART_DIR = os.path.join(REPORT_DIR, "charts")

# 可以换成其他文本文件
TARGET_TEXT_FILE = os.path.join(
    PROJECT_ROOT,
    "sample_data",
    "benchmark_site_rich",
    "index.html"
)


@dataclass
class HuffmanNode:
    freq: int
    char: Optional[str] = None
    left: Optional["HuffmanNode"] = None
    right: Optional["HuffmanNode"] = None


class HeapItem:
    def __init__(self, freq: int, order: int, node: HuffmanNode):
        self.freq = freq
        self.order = order
        self.node = node

    def __lt__(self, other):
        if self.freq == other.freq:
            return self.order < other.order
        return self.freq < other.freq


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def setup_font():
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial"]
    plt.rcParams["axes.unicode_minus"] = False


def display_char(ch: str) -> str:
    if ch == " ":
        return "[空格]"
    if ch == "\n":
        return "[换行]"
    if ch == "\t":
        return "[Tab]"
    if ch == "\r":
        return "[回车]"
    return ch


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def build_huffman_tree(freq_counter: Counter) -> Optional[HuffmanNode]:
    heap = []
    order = 0

    for ch, freq in freq_counter.items():
        node = HuffmanNode(freq=freq, char=ch)
        heapq.heappush(heap, HeapItem(freq, order, node))
        order += 1

    if not heap:
        return None

    if len(heap) == 1:
        only = heapq.heappop(heap).node
        return HuffmanNode(freq=only.freq, left=only)

    while len(heap) > 1:
        left_item = heapq.heappop(heap)
        right_item = heapq.heappop(heap)

        merged = HuffmanNode(
            freq=left_item.freq + right_item.freq,
            left=left_item.node,
            right=right_item.node
        )

        heapq.heappush(heap, HeapItem(merged.freq, order, merged))
        order += 1

    return heapq.heappop(heap).node


def build_code_table(
    node: Optional[HuffmanNode],
    prefix: str = "",
    code_table: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    if code_table is None:
        code_table = {}

    if node is None:
        return code_table

    if node.char is not None:
        code_table[node.char] = prefix if prefix else "0"
        return code_table

    build_code_table(node.left, prefix + "0", code_table)
    build_code_table(node.right, prefix + "1", code_table)

    return code_table


def save_code_table_csv(freq_counter: Counter, code_table: Dict[str, str]):
    path = os.path.join(REPORT_DIR, "huffman_code_table.csv")

    rows = []
    total = sum(freq_counter.values())

    for ch, freq in freq_counter.most_common():
        code = code_table.get(ch, "")
        rows.append({
            "字符": display_char(ch),
            "ASCII/Unicode": ord(ch),
            "出现次数": freq,
            "频率": f"{freq / total:.6f}" if total else "0",
            "Huffman编码": code,
            "编码长度": len(code)
        })

    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["字符", "ASCII/Unicode", "出现次数", "频率", "Huffman编码", "编码长度"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"已生成: {path}")


def save_frequency_chart(freq_counter: Counter):
    top_items = freq_counter.most_common(20)
    chars = [display_char(ch) for ch, _ in top_items]
    freqs = [freq for _, freq in top_items]

    colors = ["#7E93A8"] * len(chars)

    plt.figure(figsize=(11, 6), facecolor="#F5F6F8")
    ax = plt.gca()
    ax.set_facecolor("#F5F6F8")

    plt.bar(chars, freqs, color=colors)
    plt.title("Huffman 编码字符频率 Top 20", color="#4A5563", fontsize=16)
    plt.xlabel("字符", color="#4A5563")
    plt.ylabel("出现次数", color="#4A5563")
    plt.xticks(rotation=45, color="#4A5563")
    plt.yticks(color="#4A5563")
    plt.grid(axis="y", color="#D9DDE3", alpha=0.6)

    for spine in ax.spines.values():
        spine.set_color("#D9DDE3")

    plt.tight_layout()

    path = os.path.join(CHART_DIR, "huffman_frequency_top20.png")
    plt.savefig(path, dpi=200)
    plt.close()

    print(f"已生成: {path}")


def save_code_length_chart(freq_counter: Counter, code_table: Dict[str, str]):
    top_items = freq_counter.most_common(20)
    chars = [display_char(ch) for ch, _ in top_items]
    code_lengths = [len(code_table[ch]) for ch, _ in top_items]

    colors = ["#D8A7B1"] * len(chars)

    plt.figure(figsize=(11, 6), facecolor="#F5F6F8")
    ax = plt.gca()
    ax.set_facecolor("#F5F6F8")

    plt.bar(chars, code_lengths, color=colors)
    plt.title("高频字符 Huffman 编码长度 Top 20", color="#4A5563", fontsize=16)
    plt.xlabel("字符", color="#4A5563")
    plt.ylabel("编码长度 / bit", color="#4A5563")
    plt.xticks(rotation=45, color="#4A5563")
    plt.yticks(color="#4A5563")
    plt.grid(axis="y", color="#D9DDE3", alpha=0.6)

    for spine in ax.spines.values():
        spine.set_color("#D9DDE3")

    plt.tight_layout()

    path = os.path.join(CHART_DIR, "huffman_code_length_top20.png")
    plt.savefig(path, dpi=200)
    plt.close()

    print(f"已生成: {path}")


def collect_tree_nodes(
    node: Optional[HuffmanNode],
    depth: int = 0,
    index: int = 0,
    result: Optional[List[Tuple[HuffmanNode, int, int]]] = None
):
    if result is None:
        result = []

    if node is None:
        return result

    result.append((node, depth, index))

    collect_tree_nodes(node.left, depth + 1, index * 2, result)
    collect_tree_nodes(node.right, depth + 1, index * 2 + 1, result)

    return result


def assign_positions(node: Optional[HuffmanNode]):
    """
    给树节点分配坐标。
    为避免图太挤，只适合绘制小规模示例树。
    """
    positions = {}
    counter = {"x": 0}

    def dfs(n: Optional[HuffmanNode], depth: int):
        if n is None:
            return

        if n.left is None and n.right is None:
            x = counter["x"]
            counter["x"] += 1
            positions[id(n)] = (x, -depth)
            return

        dfs(n.left, depth + 1)
        dfs(n.right, depth + 1)

        child_positions = []
        if n.left is not None:
            child_positions.append(positions[id(n.left)])
        if n.right is not None:
            child_positions.append(positions[id(n.right)])

        if child_positions:
            x = sum(p[0] for p in child_positions) / len(child_positions)
        else:
            x = counter["x"]
            counter["x"] += 1

        positions[id(n)] = (x, -depth)

    dfs(node, 0)
    return positions


def draw_tree_edges(ax, node: Optional[HuffmanNode], positions):
    if node is None:
        return

    x, y = positions[id(node)]

    for child, bit in [(node.left, "0"), (node.right, "1")]:
        if child is None:
            continue

        cx, cy = positions[id(child)]

        ax.plot(
            [x, cx],
            [y, cy],
            color="#9CA8B5",
            linewidth=1.4
        )

        mid_x = (x + cx) / 2
        mid_y = (y + cy) / 2

        ax.text(
            mid_x,
            mid_y,
            bit,
            fontsize=9,
            color="#4A5563",
            ha="center",
            va="center",
            bbox=dict(
                boxstyle="round,pad=0.15",
                facecolor="#F5F6F8",
                edgecolor="#D9DDE3",
                alpha=0.9
            )
        )

        draw_tree_edges(ax, child, positions)


def draw_tree_nodes(ax, node: Optional[HuffmanNode], positions):
    if node is None:
        return

    x, y = positions[id(node)]

    if node.char is None:
        label = str(node.freq)
        face_color = "#B7C6D8"
    else:
        label = f"{display_char(node.char)}\n{node.freq}"
        face_color = "#D8A7B1"

    ax.scatter(
        [x],
        [y],
        s=1300,
        color=face_color,
        edgecolors="#FFFFFF",
        linewidths=1.6,
        zorder=3
    )

    ax.text(
        x,
        y,
        label,
        fontsize=9,
        color="#4A5563",
        ha="center",
        va="center",
        zorder=4
    )

    draw_tree_nodes(ax, node.left, positions)
    draw_tree_nodes(ax, node.right, positions)


def save_demo_tree_chart(freq_counter: Counter):
    """
    完整 HTML 文件的字符种类较多，Huffman 树会非常大。
    这里选取出现频率最高的 8 个字符构造示例树，便于展示构建逻辑。
    """
    top_counter = Counter(dict(freq_counter.most_common(8)))
    root = build_huffman_tree(top_counter)

    if root is None:
        return

    positions = assign_positions(root)

    plt.figure(figsize=(12, 7), facecolor="#F5F6F8")
    ax = plt.gca()
    ax.set_facecolor("#F5F6F8")

    draw_tree_edges(ax, root, positions)
    draw_tree_nodes(ax, root, positions)

    ax.set_title("Huffman 树构建示例（频率最高的 8 个字符）", color="#4A5563", fontsize=16)
    ax.axis("off")

    plt.tight_layout()

    path = os.path.join(CHART_DIR, "huffman_tree_demo.png")
    plt.savefig(path, dpi=200)
    plt.close()

    print(f"已生成: {path}")


def save_summary_text(text: str, freq_counter: Counter, code_table: Dict[str, str]):
    original_bits = len(text.encode("utf-8")) * 8

    # 这里是基于字符出现次数估算的 Huffman 编码 bit 数。
    # 对中文 UTF-8 字节级压缩不是完全等价，但用于解释 Huffman 原理足够。
    estimated_huffman_bits = 0
    for ch, freq in freq_counter.items():
        estimated_huffman_bits += freq * len(code_table.get(ch, ""))

    path = os.path.join(REPORT_DIR, "huffman_summary.txt")

    with open(path, "w", encoding="utf-8") as f:
        f.write("Huffman 可视化分析摘要\n")
        f.write("=" * 40 + "\n")
        f.write(f"分析文件: {TARGET_TEXT_FILE}\n")
        f.write(f"文本字符数: {len(text)}\n")
        f.write(f"不同字符种类数: {len(freq_counter)}\n")
        f.write(f"原始 UTF-8 bit 数: {original_bits}\n")
        f.write(f"估算 Huffman bit 数: {estimated_huffman_bits}\n")
        f.write("\n")
        f.write("说明：\n")
        f.write("1. 字符频率越高，Huffman 编码越短。\n")
        f.write("2. Huffman 树通过优先队列反复合并频率最低的两个节点构建。\n")
        f.write("3. 左边分支记为 0，右边分支记为 1，从根到叶子的路径即为字符编码。\n")
        f.write("4. 本文件主要用于展示核心数据结构构建过程，可作为报告中的 F7 可视化材料。\n")

    print(f"已生成: {path}")


def main():
    setup_font()
    ensure_dir(REPORT_DIR)
    ensure_dir(CHART_DIR)

    if not os.path.exists(TARGET_TEXT_FILE):
        print(f"目标文件不存在: {TARGET_TEXT_FILE}")
        return

    text = read_text(TARGET_TEXT_FILE)

    if not text:
        print("目标文件为空，无法生成 Huffman 可视化。")
        return

    freq_counter = Counter(text)
    root = build_huffman_tree(freq_counter)
    code_table = build_code_table(root)

    save_code_table_csv(freq_counter, code_table)
    save_frequency_chart(freq_counter)
    save_code_length_chart(freq_counter, code_table)
    save_demo_tree_chart(freq_counter)
    save_summary_text(text, freq_counter, code_table)

    print("\nHuffman 可视化完成。")


if __name__ == "__main__":
    main()