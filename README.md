# 网页压缩系统

本项目是一个面向网页资源的压缩与恢复系统，支持对完整网页目录中的文本资源、图片资源和其他资源进行分类处理，并生成压缩报告与可视化图表。

## 主要功能

- 网页资源扫描：递归扫描网页目录，识别 HTML、CSS、JS、JSON、XML、SVG、JPG、PNG 等资源。
- 文本资源压缩：将整站文本资源打包为 bundle，再执行字典预处理、LZ77 和 Huffman 压缩。
- 图片资源压缩：JPG 使用可控质量压缩，PNG 使用无损优化；若压缩后变大，则保留原图。
- 资源恢复：根据 manifest 将文本、图片和其他资源恢复到原目录结构。
- 压缩评估：统计原始大小、压缩后大小、压缩率、压缩耗时和解压耗时。
- 对比实验：与 ZIP、tar.gz 进行压缩率和耗时对比。
- 可视化图表：生成资源占比图、压缩大小对比图、单文件压缩率图、单文件压缩耗时图和传输时间对比图。

## 环境要求

建议使用 Python 3.10 或以上版本。

安装依赖：

```powershell
pip install -r requirements.txt
```

## 启动程序

```powershell
python main.py
```

启动后可按以下步骤演示：

1. 点击“选择网页目录”，默认会打开 `sample_data` 目录。
2. 选择 `benchmark_site_basic` 或 `benchmark_site_rich`。
3. 点击“开始压缩”。
4. 点击“恢复解压”，可选择立即打开恢复后的网页。
5. 点击“生成当前网页报告”。
6. 点击“查看当前网页图表”，查看生成的图表。

## 输出目录说明

- `output/bundles/`：文本 bundle 压缩结果。
- `output/compressed/`：图片和其他资源的压缩/保存结果，以及 `manifest.json`。
- `output/restored_from_package/`：完整恢复后的网页目录。
- `output/restored_bundle_text/`：文本 bundle 解压校验时生成的文本恢复结果。
- `output/reports/sites/<站点名>/`：当前站点的 CSV 报告和图表。
- `output/reports/charts/`：全局实验或 Huffman 可视化脚本生成的图表。

## 报告与图表

对当前网页生成报告：

```powershell
python experiments\evaluate_current_site.py sample_data\benchmark_site_rich
```

生成后可在以下目录查看：

```text
output/reports/sites/benchmark_site_rich/
```

常用图表包括：

- `total_compression_compare.png`：原始资源、自研系统、ZIP、tar.gz 的大小对比。
- `resource_type_pie.png`：文本、图片和其他资源占比。
- `file_compression_heatmap.png`：单文件压缩率排序图。
- `file_compress_time.png`：单文件压缩耗时排序图。
- `transmission_compare.png`：不同网络环境下的传输时间对比。

## 核心算法说明

文本资源压缩流程：

```text
HTML/CSS/JS 等文本资源
-> 按类型进行网页特征字典预处理
-> 打包为整站文本 bundle
-> LZ77 压缩
-> Huffman 压缩
```

图片资源压缩流程：

```text
JPG -> 质量压缩
PNG -> 无损优化
压缩无收益 -> 保留原始文件
```

恢复流程：

```text
读取 manifest.json
-> 解压文本 bundle 并按相对路径写回
-> 复制图片和其他原样保存资源
-> 定位 HTML 首页并打开验证
```
