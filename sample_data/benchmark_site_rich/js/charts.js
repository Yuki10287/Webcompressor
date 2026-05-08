(function () {
    function calculatePercent(value, total) {
        const safeTotal = total > 0 ? total : 1;
        return Math.round((value / safeTotal) * 100);
    }

    function formatChartValue(value, suffix) {
        const unit = suffix || "%";
        return String(value) + unit;
    }

    function createBarRow(item) {
        const row = document.createElement("div");
        row.classList.add("chart-bar-row");

        const label = document.createElement("div");
        label.classList.add("comparison-cell");
        label.textContent = item.label + " - " + formatChartValue(item.value, item.suffix);
        row.appendChild(label);

        const track = document.createElement("div");
        track.classList.add("chart-track");

        const fill = document.createElement("div");
        fill.classList.add("chart-bar-fill");
        fill.style.width = formatChartValue(item.percent, "%");
        fill.textContent = formatChartValue(item.percent, "%");
        track.appendChild(fill);

        row.appendChild(track);
        return row;
    }

    function createBarChart(title, items, themeClass) {
        const panel = document.createElement("section");
        panel.classList.add("chart-panel");
        if (themeClass) {
            panel.classList.add(themeClass);
        }

        const heading = document.createElement("h3");
        heading.classList.add("card-title");
        heading.textContent = title;
        panel.appendChild(heading);

        items.forEach(function (item) {
            panel.appendChild(createBarRow(item));
        });

        return panel;
    }

    function createPieLegend(items) {
        const legend = document.createElement("div");
        legend.classList.add("chart-legend");

        items.forEach(function (item) {
            const line = document.createElement("div");
            line.classList.add("comparison-row");

            const swatch = document.createElement("div");
            swatch.classList.add("comparison-cell");
            swatch.textContent = item.label;
            swatch.style.width = "100%";
            swatch.style.backgroundColor = item.color;
            swatch.style.color = "#ffffff";
            swatch.style.padding = "10px 12px";
            swatch.style.borderRadius = "12px";

            const value = document.createElement("div");
            value.classList.add("comparison-cell");
            value.textContent = formatChartValue(item.percent, "%") + " · " + formatChartValue(item.value, item.suffix);

            line.appendChild(swatch);
            line.appendChild(value);
            legend.appendChild(line);
        });

        return legend;
    }

    function renderCompressionBars(container) {
        const total = 100;
        const items = [
            { label: "HTML 压缩率", value: 42, percent: calculatePercent(42, total), suffix: "%" },
            { label: "CSS 压缩率", value: 38, percent: calculatePercent(38, total), suffix: "%" },
            { label: "JS 压缩率", value: 35, percent: calculatePercent(35, total), suffix: "%" },
            { label: "图片压缩率", value: 27, percent: calculatePercent(27, total), suffix: "%" }
        ];
        const chart = createBarChart("压缩率示意", items, "transition-normal");
        container.appendChild(chart);
        return items;
    }

    function renderTransmissionBars(container) {
        const total = 200;
        const items = [
            { label: "原始传输时间", value: 180, percent: calculatePercent(180, total), suffix: " ms" },
            { label: "预处理后传输时间", value: 132, percent: calculatePercent(132, total), suffix: " ms" },
            { label: "压缩后传输时间", value: 98, percent: calculatePercent(98, total), suffix: " ms" },
            { label: "恢复后首屏时间", value: 116, percent: calculatePercent(116, total), suffix: " ms" }
        ];
        const chart = createBarChart("传输时间示意", items, "transition-normal");
        container.appendChild(chart);
        return items;
    }

    function createSummary(text) {
        const summary = document.createElement("div");
        summary.classList.add("note-box");
        summary.textContent = text;
        return summary;
    }

    function initChartsDemo(root) {
        const scope = root || document;
        const mount = scope.querySelector("[data-chart-demo]");
        if (!mount) {
            return false;
        }
        mount.innerHTML = "";

        const compressionItems = renderCompressionBars(mount);
        const transmissionItems = renderTransmissionBars(mount);
        const combinedBase = transmissionItems[0].value + transmissionItems[1].value + transmissionItems[2].value + transmissionItems[3].value;

        const legendItems = [
            { label: "文本压缩", value: compressionItems[0].value, percent: compressionItems[0].percent, suffix: "%", color: "#1f5fbf" },
            { label: "样式压缩", value: compressionItems[1].value, percent: compressionItems[1].percent, suffix: "%", color: "#6c52c9" },
            { label: "脚本压缩", value: compressionItems[2].value, percent: compressionItems[2].percent, suffix: "%", color: "#3f8c6b" },
            { label: "图片压缩", value: compressionItems[3].value, percent: compressionItems[3].percent, suffix: "%", color: "#d67d37" },
            { label: "传输占比", value: transmissionItems[2].value, percent: calculatePercent(transmissionItems[2].value, combinedBase), suffix: " ms", color: "#2b7b93" }
        ];

        mount.appendChild(createPieLegend(legendItems));
        mount.appendChild(createSummary("图表示意采用原生 DOM 节点生成，条宽由 style.width 控制，适合在本地静态页面中模拟压缩率和传输率展示。"));
        mount.appendChild(createSummary("这些图表不依赖第三方库，核心目的是增加重复脚本结构、重复条形节点和重复说明文本。"));

        return true;
    }

    window.RichCharts = {
        createBarChart: createBarChart,
        createPieLegend: createPieLegend,
        renderCompressionBars: renderCompressionBars,
        renderTransmissionBars: renderTransmissionBars,
        calculatePercent: calculatePercent,
        formatChartValue: formatChartValue,
        initChartsDemo: initChartsDemo
    };

    document.addEventListener("DOMContentLoaded", function () {
        const body = document.querySelector("body");
        if (!body) {
            return;
        }
        if (body.dataset.page === "docs" || body.dataset.page === "pricing") {
            initChartsDemo(document);
        }
    });
}());
