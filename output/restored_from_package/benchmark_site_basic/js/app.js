(function () {
    var data = window.BenchmarkDataBasic || {};
    var utils = window.BenchmarkUtilsBasic || {};

    function highlightNav() {
        var currentPage = document.body.getAttribute("data-page");
        var navLinks = document.querySelectorAll("[data-nav]");
        navLinks.forEach(function (link) {
            if (link.getAttribute("href").indexOf(currentPage) !== -1 || (currentPage === "index" && link.getAttribute("href") === "index.html")) {
                link.classList.add("btn-secondary");
            } else {
                link.classList.remove("btn-secondary");
            }
        });
    }

    function logButtonClicks() {
        var buttons = document.querySelectorAll(".btn");
        buttons.forEach(function (button) {
            button.addEventListener("click", function () {
                console.log("button click", button.textContent.trim());
            });
        });
    }

    function bindForms() {
        var forms = document.querySelectorAll("[data-validate-form]");
        forms.forEach(function (form) {
            form.addEventListener("submit", function (event) {
                event.preventDefault();
                var nameInput = form.querySelector('input[name="name"]');
                var emailInput = form.querySelector('input[name="email"]');
                var valid = true;
                if (nameInput && !nameInput.value.trim()) {
                    nameInput.classList.add("is-invalid");
                    valid = false;
                } else if (nameInput) {
                    nameInput.classList.remove("is-invalid");
                }
                if (emailInput && emailInput.value.indexOf("@") === -1) {
                    emailInput.classList.add("is-invalid");
                    valid = false;
                } else if (emailInput) {
                    emailInput.classList.remove("is-invalid");
                }
                console.log("form submit", form.className, valid);
            });
        });
    }

    function renderFeatures() {
        var featureGrid = document.querySelector("#feature-grid");
        if (!featureGrid) {
            return;
        }
        featureGrid.innerHTML = data.features.map(function (item) {
            return '<article class="feature-card">' +
                utils.createBadge(item.badge) +
                utils.createCardTitle(item.title + " / " + item.subtitle) +
                utils.createCardText(item.description) +
                '<p class="card-text">分类：' + utils.escapeHtml(item.category) + '，标签：' + utils.escapeHtml(item.tag) + "</p>" +
                '<button class="btn btn-secondary" type="button">' + utils.escapeHtml(item.buttonText) + "</button>" +
                "</article>";
        }).join("");
    }

    function renderNews() {
        var newsGrid = document.querySelector("#news-grid");
        if (!newsGrid) {
            return;
        }
        newsGrid.innerHTML = data.news.map(function (item) {
            return '<article class="news-card">' +
                utils.createBadge(item.badge) +
                utils.createCardTitle(item.title + " / " + item.subtitle) +
                utils.createCardText(item.description) +
                '<button class="btn btn-secondary" type="button">' + utils.escapeHtml(item.buttonText) + "</button>" +
                "</article>";
        }).join("");
    }

    function renderStats() {
        var statGrid = document.querySelector("#stat-grid");
        if (!statGrid) {
            return;
        }
        statGrid.innerHTML = data.stats.map(function (item) {
            return '<article class="stat-card">' +
                utils.createBadge(item.badge) +
                utils.createCardTitle(item.title) +
                '<p class="product-price">' + utils.escapeHtml(String(item.price)) + "</p>" +
                utils.createCardText(item.description) +
                "</article>";
        }).join("");
    }

    function renderTeam() {
        var teamGrid = document.querySelector("#team-grid");
        if (!teamGrid) {
            return;
        }
        teamGrid.innerHTML = data.team.map(function (item) {
            return '<article class="team-card">' +
                '<img class="rounded" src="images/avatar.jpg" alt="成员头像">' +
                '<h3 class="team-name">' + utils.escapeHtml(item.title) + "</h3>" +
                '<p class="team-role">' + utils.escapeHtml(item.subtitle) + "</p>" +
                '<p class="card-text">' + utils.escapeHtml(item.description) + "</p>" +
                "</article>";
        }).join("");
    }

    function renderFaq() {
        var faqGrid = document.querySelector("#faq-grid");
        if (!faqGrid) {
            return;
        }
        faqGrid.innerHTML = data.faq.map(function (item) {
            return '<article class="faq-item">' +
                '<h3 class="faq-question">' + utils.escapeHtml(item.title) + "</h3>" +
                '<p class="faq-answer">' + utils.escapeHtml(item.description) + "</p>" +
                "</article>";
        }).join("");
    }

    function renderProducts(filterName) {
        var productGrid = document.querySelector("#product-grid");
        if (!productGrid) {
            return;
        }
        var filteredProducts = (data.products || []).filter(function (item) {
            return filterName === "all" || item.category === filterName;
        });
        productGrid.innerHTML = filteredProducts.map(function (item) {
            return '<article class="product-card">' +
                utils.createBadge(item.badge) +
                '<span class="product-tag">' + utils.escapeHtml(item.tag) + "</span>" +
                '<h3 class="product-title">' + utils.escapeHtml(item.title) + "</h3>" +
                '<p class="card-text">' + utils.escapeHtml(item.description) + "</p>" +
                '<p class="product-price">' + utils.formatPrice(item.price) + "</p>" +
                '<button class="btn btn-primary" type="button">' + utils.escapeHtml(item.buttonText) + "</button>" +
                "</article>";
        }).join("");
        logButtonClicks();
    }

    function bindFilters() {
        var filterButtons = document.querySelectorAll("[data-filter]");
        filterButtons.forEach(function (button) {
            button.addEventListener("click", function () {
                document.querySelectorAll("[data-filter]").forEach(function (item) {
                    item.classList.remove("btn-primary");
                });
                button.classList.add("btn-primary");
                renderProducts(button.getAttribute("data-filter"));
                console.log("filter click", button.getAttribute("data-filter"));
            });
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        highlightNav();
        renderFeatures();
        renderNews();
        renderStats();
        renderTeam();
        renderFaq();
        renderProducts("all");
        bindFilters();
        bindForms();
        logButtonClicks();
        document.querySelectorAll(".faq-item").forEach(function (item) {
            item.addEventListener("click", function () {
                item.classList.add("shadow-sm");
                console.log("faq click", item.textContent.trim().slice(0, 16));
            });
        });
    });
}());
