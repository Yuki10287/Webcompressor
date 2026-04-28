(function () {
    var utils = window.BenchmarkUtilsRich;

    function renderFeatureCard(item) {
        return '<article class="feature-card">' + utils.renderBadge(item.badge) + '<h3 class="card-title">' + utils.escapeHtml(item.title) + '</h3><p class="card-text">' + utils.escapeHtml(item.description) + '</p><p class="card-text">' + utils.escapeHtml(item.subtitle) + '</p></article>';
    }
    function renderServiceCard(item) {
        return '<article class="service-card">' + utils.renderTag(item.tag) + '<h3 class="service-title">' + utils.escapeHtml(item.title) + '</h3><p class="service-text">' + utils.escapeHtml(item.longDescription) + '</p><button class="button button-secondary" type="button">' + utils.escapeHtml(item.actionText) + '</button></article>';
    }
    function renderCaseCard(item) {
        return '<article class="case-card">' + utils.renderBadge(item.badge) + '<h3 class="card-title">' + utils.escapeHtml(item.title) + '</h3><p class="card-text">' + utils.escapeHtml(item.longDescription) + '</p><p class="card-text">' + utils.escapeHtml(item.category) + '</p></article>';
    }
    function renderProductCard(item) {
        return '<article class="product-card">' + utils.renderBadge(item.badge) + '<img src="' + utils.escapeHtml(item.image) + '" alt="' + utils.escapeHtml(item.title) + '"><h3 class="product-title">' + utils.escapeHtml(item.title) + '</h3><p class="card-text">' + utils.escapeHtml(item.description) + '</p><p class="card-text">' + utils.formatCurrency(item.price) + '</p><button class="button button-primary" type="button">' + utils.escapeHtml(item.actionText) + '</button></article>';
    }
    function renderGalleryCard(item) {
        return '<article class="gallery-card">' + utils.renderTag(item.tag) + '<img src="' + utils.escapeHtml(item.image) + '" alt="' + utils.escapeHtml(item.title) + '"><h3 class="card-title">' + utils.escapeHtml(item.title) + '</h3><p class="card-text">' + utils.escapeHtml(item.description) + '</p></article>';
    }
    function renderFaqItem(item) {
        return '<article class="accordion-item faq-item"><h3 class="card-title">' + utils.escapeHtml(item.title) + '</h3><p class="faq-answer">' + utils.escapeHtml(item.longDescription) + '</p></article>';
    }
    function renderReviewCard(item) {
        return '<article class="review-card">' + utils.renderBadge(item.highlight) + '<h3 class="card-title">' + utils.escapeHtml(item.title) + '</h3><p class="card-text">' + utils.escapeHtml(item.description) + '</p><p class="card-text">' + utils.formatDate(item.id) + '</p></article>';
    }
    function renderTestimonialCard(item) {
        return '<article class="testimonial-card">' + utils.renderBadge(item.highlight) + '<h3 class="card-title">' + utils.escapeHtml(item.title) + '</h3><p class="card-text">' + utils.escapeHtml(item.longDescription) + '</p><p class="card-text">' + utils.escapeHtml(item.subtitle) + '</p></article>';
    }
    window.BenchmarkDomRich = {
        renderFeatureCard: renderFeatureCard,
        renderServiceCard: renderServiceCard,
        renderCaseCard: renderCaseCard,
        renderProductCard: renderProductCard,
        renderGalleryCard: renderGalleryCard,
        renderFaqItem: renderFaqItem,
        renderReviewCard: renderReviewCard,
        renderTestimonialCard: renderTestimonialCard
    };
}());
