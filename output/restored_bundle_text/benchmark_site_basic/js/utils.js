(function () {
    function formatPrice(value) {
        return "¥" + Number(value || 0).toFixed(2);
    }

    function createBadge(text) {
        return '<span class="badge">' + escapeHtml(text || "") + "</span>";
    }

    function createCardTitle(text) {
        return '<h3 class="card-title">' + escapeHtml(text || "") + "</h3>";
    }

    function createCardText(text) {
        return '<p class="card-text">' + escapeHtml(text || "") + "</p>";
    }

    function clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
    }

    function debounce(fn, wait) {
        var timer = null;
        return function () {
            var context = this;
            var args = arguments;
            clearTimeout(timer);
            timer = setTimeout(function () {
                fn.apply(context, args);
            }, wait);
        };
    }

    function throttle(fn, wait) {
        var lastTime = 0;
        return function () {
            var now = Date.now();
            if (now - lastTime >= wait) {
                lastTime = now;
                fn.apply(this, arguments);
            }
        };
    }

    function escapeHtml(text) {
        return String(text || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    window.BenchmarkUtilsBasic = {
        formatPrice: formatPrice,
        createBadge: createBadge,
        createCardTitle: createCardTitle,
        createCardText: createCardText,
        clamp: clamp,
        debounce: debounce,
        throttle: throttle,
        escapeHtml: escapeHtml
    };
}());
