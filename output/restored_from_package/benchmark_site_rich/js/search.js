(function () {
    function normalizeKeyword(keyword) {
        const value = (keyword || "").replace(/\s+/g, " ").trim().toLowerCase();
        return value;
    }

    function getCardText(card) {
        const titleNode = card.querySelector(".article-title") || card.querySelector(".faq-question");
        const summaryNode = card.querySelector(".article-summary") || card.querySelector(".faq-answer");
        const tagNode = card.querySelector(".article-tag") || card.querySelector(".faq-tag");
        const titleText = titleNode ? titleNode.textContent : "";
        const summaryText = summaryNode ? summaryNode.textContent : "";
        const tagText = tagNode ? tagNode.textContent : "";
        const dataText = card.dataset.tags || "";
        return [titleText, summaryText, tagText, dataText].join(" ").toLowerCase();
    }

    function escapeKeyword(keyword) {
        return keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    function resetNode(node) {
        if (!node) {
            return false;
        }
        if (node.dataset.originalText) {
            node.innerHTML = node.dataset.originalText;
            return true;
        }
        return false;
    }

    function clearSearchResult(root) {
        const scope = root || document;
        const cards = scope.querySelectorAll("[data-search-card]");
        cards.forEach(function (card) {
            card.classList.remove("is-hidden");
            card.classList.remove("is-match");
            const titleNode = card.querySelector(".article-title") || card.querySelector(".faq-question");
            const summaryNode = card.querySelector(".article-summary") || card.querySelector(".faq-answer");
            resetNode(titleNode);
            resetNode(summaryNode);
        });
        return cards.length;
    }

    function highlightKeyword(card, keyword) {
        const normalized = normalizeKeyword(keyword);
        if (!normalized) {
            return false;
        }
        const expression = new RegExp("(" + escapeKeyword(normalized) + ")", "gi");
        const titleNode = card.querySelector(".article-title") || card.querySelector(".faq-question");
        const summaryNode = card.querySelector(".article-summary") || card.querySelector(".faq-answer");
        [titleNode, summaryNode].forEach(function (node) {
            if (!node) {
                return;
            }
            if (!node.dataset.originalText) {
                node.dataset.originalText = node.innerHTML;
            }
            const plainText = node.textContent;
            if (plainText.toLowerCase().indexOf(normalized) !== -1) {
                node.innerHTML = plainText.replace(expression, '<mark class="keyword-mark">$1</mark>');
            } else {
                node.innerHTML = plainText;
            }
        });
        return true;
    }

    function createSearchSummary(totalCount, matchCount, keyword) {
        const normalized = normalizeKeyword(keyword);
        if (!normalized) {
            return "请输入关键字筛选当前页面内容。";
        }
        if (matchCount === 0) {
            return "未找到与 “" + normalized + "” 相关的结果，共检查 " + totalCount + " 个条目。";
        }
        return "关键字 “" + normalized + "” 匹配到 " + matchCount + " / " + totalCount + " 个条目。";
    }

    function updateCardState(card, isMatch, keyword) {
        const titleNode = card.querySelector(".article-title") || card.querySelector(".faq-question");
        const summaryNode = card.querySelector(".article-summary") || card.querySelector(".faq-answer");
        if (isMatch) {
            card.classList.add("is-match");
            card.classList.remove("is-hidden");
            highlightKeyword(card, keyword);
            return true;
        }
        card.classList.add("is-hidden");
        card.classList.remove("is-match");
        resetNode(titleNode);
        resetNode(summaryNode);
        return false;
    }

    function filterCards(root, keyword) {
        const scope = root || document;
        const normalized = normalizeKeyword(keyword);
        const cards = scope.querySelectorAll("[data-search-card]");
        let matchCount = 0;

        cards.forEach(function (card) {
            const text = getCardText(card);
            card.classList.remove("is-hidden");
            card.classList.remove("is-match");
            if (!normalized) {
                const titleNode = card.querySelector(".article-title") || card.querySelector(".faq-question");
                const summaryNode = card.querySelector(".article-summary") || card.querySelector(".faq-answer");
                resetNode(titleNode);
                resetNode(summaryNode);
                return;
            }
            if (text.indexOf(normalized) !== -1) {
                if (updateCardState(card, true, normalized)) {
                    matchCount += 1;
                }
                return;
            }
            updateCardState(card, false, normalized);
        });

        return {
            totalCount: cards.length,
            matchCount: matchCount,
            keyword: normalized
        };
    }

    function bindSearchInput(root) {
        const scope = root || document;
        const searchInput = scope.querySelector("[data-search-input]");
        const summaryNode = scope.querySelector("[data-search-summary]");
        const clearButton = scope.querySelector("[data-search-clear]");
        if (!searchInput) {
            return false;
        }

        searchInput.addEventListener("input", function () {
            const result = filterCards(scope, searchInput.value);
            if (summaryNode) {
                summaryNode.textContent = createSearchSummary(result.totalCount, result.matchCount, result.keyword);
            }
        });

        searchInput.addEventListener("focus", function () {
            if (summaryNode) {
                summaryNode.classList.add("is-focus");
            }
        });

        searchInput.addEventListener("blur", function () {
            if (summaryNode) {
                summaryNode.classList.remove("is-focus");
            }
        });

        if (clearButton) {
            clearButton.addEventListener("click", function () {
                searchInput.value = "";
                clearSearchResult(scope);
                if (summaryNode) {
                    summaryNode.textContent = createSearchSummary(
                        scope.querySelectorAll("[data-search-card]").length,
                        scope.querySelectorAll("[data-search-card]").length,
                        ""
                    );
                }
            });
        }
        return true;
    }

    function initPageSearch(root) {
        const scope = root || document;
        const hasInput = scope.querySelector("[data-search-input]");
        const hasCards = scope.querySelectorAll("[data-search-card]");
        if (!hasInput || !hasCards.length) {
            return false;
        }
        clearSearchResult(scope);
        bindSearchInput(scope);
        const summaryNode = scope.querySelector("[data-search-summary]");
        if (summaryNode) {
            summaryNode.textContent = createSearchSummary(hasCards.length, hasCards.length, "");
        }
        return true;
    }

    window.RichSearch = {
        normalizeKeyword: normalizeKeyword,
        filterCards: filterCards,
        highlightKeyword: highlightKeyword,
        bindSearchInput: bindSearchInput,
        clearSearchResult: clearSearchResult,
        createSearchSummary: createSearchSummary,
        initPageSearch: initPageSearch
    };

    document.addEventListener("DOMContentLoaded", function () {
        const body = document.querySelector("body");
        if (!body) {
            return;
        }
        if (body.dataset.page === "faq" || body.dataset.page === "blog") {
            initPageSearch(document);
        }
    });
}());
