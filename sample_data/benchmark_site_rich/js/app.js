(function () {
    var data = window.BenchmarkDataRich || {};
    var utils = window.BenchmarkUtilsRich;
    var dom = window.BenchmarkDomRich;

    function setHtml(selector, html) {
        var node = utils.qs(selector);
        if (node) { node.innerHTML = html; }
    }

    function highlightNav() {
        var page = document.body.getAttribute("data-page");
        utils.qsa("[data-nav]").forEach(function (link) {
            if (link.getAttribute("href").indexOf(page) !== -1 || (page === "index" && link.getAttribute("href") === "index.html")) {
                link.classList.add("button-primary");
            } else {
                link.classList.remove("button-primary");
            }
        });
    }

    function bindButtons() {
        utils.qsa(".button").forEach(function (button) {
            utils.on(button, "click", function () {
                console.log("button click", button.textContent.trim());
            });
        });
    }

    function bindForms() {
        utils.qsa("[data-validate-form]").forEach(function (form) {
            utils.on(form, "submit", function (event) {
                event.preventDefault();
                var nameInput = utils.qs('input[name="name"]', form);
                var emailInput = utils.qs('input[name="email"]', form);
                if (nameInput && !nameInput.value.trim()) { nameInput.classList.add("is-invalid"); } else if (nameInput) { nameInput.classList.remove("is-invalid"); }
                if (emailInput && emailInput.value.indexOf("@") === -1) { emailInput.classList.add("is-invalid"); } else if (emailInput) { emailInput.classList.remove("is-invalid"); }
                console.log("form submit", form.className);
            });
        });
    }

    function renderHome() {
        setHtml("#rich-feature-grid", data.features.map(dom.renderFeatureCard).join(""));
        setHtml("#rich-service-grid", data.services.slice(0, 12).map(dom.renderServiceCard).join(""));
        setHtml("#rich-case-grid", data.cases.map(dom.renderCaseCard).join(""));
        setHtml("#rich-testimonial-grid", data.testimonials.map(dom.renderTestimonialCard).join(""));
    }

    function renderAbout() {
        setHtml("#value-grid", data.values.map(function (item) {
            return '<article class="value-card">' + utils.renderBadge(item.badge) + '<h3 class="card-title">' + utils.escapeHtml(item.title) + '</h3><p class="card-text">' + utils.escapeHtml(item.longDescription) + '</p></article>';
        }).join(""));
        setHtml("#timeline-grid", data.services.slice(0, 12).map(function (item) {
            return '<article class="process-step timeline-item"><h3 class="card-title">' + utils.escapeHtml(item.title) + '</h3><p class="card-text">' + utils.escapeHtml(item.description) + '</p></article>';
        }).join(""));
        setHtml("#rich-team-grid", data.team.map(function (item, index) {
            var avatar = "images/avatar" + ((index % 3) + 1) + ".jpg";
            return '<article class="team-card"><img src="' + avatar + '" alt="' + utils.escapeHtml(item.title) + '"><h3 class="card-title">' + utils.escapeHtml(item.title) + '</h3><p class="card-text">' + utils.escapeHtml(item.subtitle) + '</p><p class="card-text">' + utils.escapeHtml(item.description) + '</p></article>';
        }).join(""));
        setHtml("#rich-faq-grid", data.faq.map(dom.renderFaqItem).join(""));
    }

    function renderServices() {
        setHtml("#services-page-grid", data.services.map(dom.renderServiceCard).join(""));
        setHtml("#pricing-grid", data.services.slice(0, 8).map(function (item) {
            return '<article class="pricing-card"><h3 class="card-title">' + utils.escapeHtml(item.title) + '</h3><p class="card-text">' + utils.escapeHtml(item.subtitle) + '</p><p class="card-text">' + utils.formatCurrency(item.price) + '</p><button class="button button-primary" type="button">' + utils.escapeHtml(item.actionText) + '</button></article>';
        }).join(""));
        setHtml("#process-grid", data.services.slice(0, 10).map(function (item) {
            return '<article class="process-step"><h3 class="card-title">' + utils.escapeHtml(item.title) + '</h3><p class="card-text">' + utils.escapeHtml(item.longDescription) + '</p></article>';
        }).join(""));
        setHtml("#comparison-grid", data.services.slice(0, 6).map(function (item) {
            return '<article class="comparison-row"><h3 class="card-title">' + utils.escapeHtml(item.title) + '</h3><p class="card-text">' + utils.escapeHtml(item.highlight) + " / " + utils.escapeHtml(item.category) + '</p></article>';
        }).join(""));
    }

    function renderProducts(filterName) {
        var list = data.products.filter(function (item) { return filterName === "all" || item.category === filterName; });
        setHtml("#products-page-grid", list.map(dom.renderProductCard).join(""));
        setHtml("#bundle-grid", data.bundles.map(function (item) {
            return '<article class="bundle-card"><h3 class="card-title">' + utils.escapeHtml(item.title) + '</h3><p class="card-text">' + utils.escapeHtml(item.longDescription) + '</p><p class="card-text">' + utils.formatCurrency(item.price) + '</p></article>';
        }).join(""));
        setHtml("#products-table", '<thead><tr><th>产品</th><th>分类</th><th>标签</th><th>价格</th></tr></thead><tbody>' + data.products.slice(0, 12).map(function (item) {
            return '<tr><td>' + utils.escapeHtml(item.title) + '</td><td>' + utils.escapeHtml(item.category) + '</td><td>' + utils.escapeHtml(item.tag) + '</td><td>' + utils.formatCurrency(item.price) + '</td></tr>';
        }).join("") + "</tbody>");
        bindButtons();
    }

    function bindProductFilter() {
        utils.qsa("[data-product-filter]").forEach(function (button) {
            utils.on(button, "click", function () {
                var filter = button.getAttribute("data-product-filter");
                utils.qsa("[data-product-filter]").forEach(function (item) {
                    item.classList.remove("button-primary");
                    item.classList.add("button-secondary");
                });
                button.classList.add("button-primary");
                button.classList.remove("button-secondary");
                renderProducts(filter);
                console.log("product filter", filter);
            });
        });
    }

    function renderGallery() {
        setHtml("#gallery-page-grid", data.gallery.map(function (item, index) {
            item.image = index % 2 === 0 ? "images/gallery1.jpg" : "images/gallery2.jpg";
            return dom.renderGalleryCard(item);
        }).join(""));
        setHtml("#review-grid", data.reviews.map(dom.renderReviewCard).join(""));
    }

    function renderContact() {
        setHtml("#office-grid", data.offices.map(function (item) {
            return '<article class="office-card"><h3 class="card-title">' + utils.escapeHtml(item.title) + '</h3><p class="card-text">' + utils.escapeHtml(item.subtitle) + '</p><p class="card-text">' + utils.escapeHtml(item.longDescription) + '</p></article>';
        }).join(""));
        setHtml("#contact-faq-grid", data.faq.map(dom.renderFaqItem).join(""));
    }

    document.addEventListener("DOMContentLoaded", function () {
        highlightNav();
        renderHome();
        renderAbout();
        renderServices();
        renderProducts("all");
        bindProductFilter();
        renderGallery();
        renderContact();
        bindForms();
        bindButtons();
        if (window.BenchmarkGalleryRich) {
            window.BenchmarkGalleryRich.initGalleryPage();
        }
        utils.qsa(".accordion-item").forEach(function (item) {
            utils.on(item, "click", function () {
                item.classList.toggle("shadow-lg");
                console.log("accordion click", item.textContent.trim().slice(0, 20));
            });
        });
    });
}());
