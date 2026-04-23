(function () {
    function qs(selector, scope) { return (scope || document).querySelector(selector); }
    function qsa(selector, scope) { return Array.prototype.slice.call((scope || document).querySelectorAll(selector)); }
    function on(node, type, handler) { if (node) { node.addEventListener(type, handler); } }
    function off(node, type, handler) { if (node) { node.removeEventListener(type, handler); } }
    function createNode(tag, className, html) {
        var node = document.createElement(tag);
        if (className) { node.className = className; }
        if (html) { node.innerHTML = html; }
        return node;
    }
    function renderBadge(text) { return '<span class="badge">' + escapeHtml(text) + "</span>"; }
    function renderTag(text) { return '<span class="tag">' + escapeHtml(text) + "</span>"; }
    function formatCurrency(value) { return "¥" + Number(value || 0).toFixed(2); }
    function formatDate(index) { return "2026-04-" + String((index % 28) + 1).padStart(2, "0"); }
    function slugify(text) { return String(text || "").toLowerCase().replace(/\s+/g, "-"); }
    function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }
    function debounce(fn, wait) {
        var timer = null;
        return function () {
            var args = arguments;
            var context = this;
            clearTimeout(timer);
            timer = setTimeout(function () { fn.apply(context, args); }, wait);
        };
    }
    function throttle(fn, wait) {
        var last = 0;
        return function () {
            var now = Date.now();
            if (now - last >= wait) {
                last = now;
                fn.apply(this, arguments);
            }
        };
    }
    function groupBy(list, key) {
        return (list || []).reduce(function (acc, item) {
            var value = item[key];
            if (!acc[value]) { acc[value] = []; }
            acc[value].push(item);
            return acc;
        }, {});
    }
    function chunkArray(list, size) {
        var result = [];
        for (var i = 0; i < list.length; i += size) {
            result.push(list.slice(i, i + size));
        }
        return result;
    }
    function escapeHtml(text) {
        return String(text || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }
    window.BenchmarkUtilsRich = {
        qs: qs, qsa: qsa, on: on, off: off, createNode: createNode,
        renderBadge: renderBadge, renderTag: renderTag, formatCurrency: formatCurrency, formatDate: formatDate,
        slugify: slugify, clamp: clamp, debounce: debounce, throttle: throttle, groupBy: groupBy, chunkArray: chunkArray,
        escapeHtml: escapeHtml
    };
}());
