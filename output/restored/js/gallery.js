(function () {
    var utils = window.BenchmarkUtilsRich;

    function bindGalleryFilter() {
        var filterButtons = utils.qsa("[data-gallery-filter]");
        var cards = utils.qsa("#gallery-page-grid .gallery-card");
        filterButtons.forEach(function (button) {
            utils.on(button, "click", function () {
                var filter = button.getAttribute("data-gallery-filter");
                utils.qsa("[data-gallery-filter]").forEach(function (item) {
                    item.classList.remove("button-primary");
                    item.classList.add("button-secondary");
                });
                button.classList.add("button-primary");
                button.classList.remove("button-secondary");
                cards = utils.qsa("#gallery-page-grid .gallery-card");
                cards.forEach(function (card) {
                    var cardText = card.textContent;
                    if (filter === "all" || cardText.indexOf(filter) !== -1) {
                        card.classList.remove("is-hidden");
                    } else {
                        card.classList.add("is-hidden");
                    }
                });
            });
        });
    }

    function bindGalleryPreview() {
        utils.qsa("#gallery-page-grid .gallery-card img").forEach(function (image) {
            utils.on(image, "click", function () {
                image.classList.add("shadow-lg");
                console.log("gallery preview", image.getAttribute("src"));
            });
        });
    }

    function initGalleryPage() {
        if (!utils.qs("#gallery-page-grid")) {
            return;
        }
        bindGalleryFilter();
        bindGalleryPreview();
    }

    window.BenchmarkGalleryRich = {
        initGalleryPage: initGalleryPage
    };
}());
