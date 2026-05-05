// Card Hover/Modal functionality for Gehenna Web
// Based on KRCG: https://static.krcg.org/web/krcg.js

(function () {
    'use strict';

    const BASE_URL = 'https://static.krcg.org/card/';
    const CARD_BACK = 'https://static.krcg.org/cardback';

    // Cache for card names to avoid multiple lookups
    const cardCache = new Map();
    // Current hovered element
    let currentHover = null;
    // Hover timeout
    let hoverTimeout = null;
    // Modal element
    let modalEl = null;
    let modalImg = null;

    // Initialize on DOM ready
    document.addEventListener('DOMContentLoaded', init);

    function init() {
        createModal();
        createStyles();
        setupCardLinks();
        setupCardImages();
    }

    function createStyles() {
        const css = `
            .card-hover {
                cursor: pointer;
                position: relative;
            }
            .card-hover:hover {
                outline: 2px solid #0d6efd;
                outline-offset: 2px;
            }
            #card-modal {
                display: none;
                position: fixed;
                z-index: 9999;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.85);
                justify-content: center;
                align-items: center;
            }
            #card-modal.show {
                display: flex;
            }
            #card-modal img {
                max-width: 95vw;
                max-height: 95vh;
                object-fit: contain;
            }
            #card-modal .close-btn {
                position: absolute;
                top: 20px;
                right: 30px;
                color: white;
                font-size: 40px;
                cursor: pointer;
            }
            .card-tooltip {
                position: absolute;
                z-index: 9998;
                display: none;
                background: white;
                padding: 5px;
                border-radius: 4px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }
            .card-tooltip img {
                width: 150px;
                height: auto;
            }
        `;
        const style = document.createElement('style');
        style.textContent = css;
        document.head.appendChild(style);
    }

    function createModal() {
        modalEl = document.createElement('div');
        modalEl.id = 'card-modal';
        modalEl.innerHTML = '<span class="close-btn">&times;</span><img src="" alt="Card">';
        modalEl.addEventListener('click', closeModal);
        document.body.appendChild(modalEl);
    }

    function closeModal() {
        modalEl.classList.remove('show');
    }

    // Extract card name from text or data attribute
    function getCardName(el) {
        // Try data attribute first
        let name = el.dataset.cardName || el.dataset.card;
        if (name) return name.normalizeCardName(name);

        // Try title attribute (often contains card name)
        const title = el.title || el.textContent;
        if (title) {
            // Clean up the name
            name = title.trim()
                .replace(/\s+/g, ' ')
                .replace(/^\d+\)\s*/, '')
                .replace(/ \(.*?\)/, '')
                .replace(/\s*\(\d+\)/, '')
                .replace(/^\d+\s*/, '');
            return name.normalizeCardName(name);
        }
        return null;
    }

    // Normalize card name for URL
    String.prototype.normalizeCardName = function () {
        return this.toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '') // Remove accents
            .replace(/[^a-z0-9]/g, '') // Keep only letters and numbers
            .replace(/^(the|an?)\s*/, ''); // Remove leading "the", "a", "an"
    };

    // Get card image URL
    function getCardImageUrl(name, options = {}) {
        if (!name) return getCardBackUrl(options.isCrypt);

        const baseName = name.normalizeCardName();
        let url = BASE_URL + baseName + '.webp';

        if (options.group) url = BASE_URL + baseName + 'g' + options.group + '.webp';
        if (options.advanced) url = BASE_URL + baseName + (options.group ? 'g' + options.group : 'g2') + 'adv.webp';

        return url;
    }

    function getCardBackUrl(isCrypt) {
        return CARD_BACK + (isCrypt ? 'crypt' : 'library') + '.jpg';
    }

    // Check if image exists
    function checkImage(url) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => resolve(true);
            img.onerror = () => resolve(false);
            img.src = url;
        });
    }

    // Setup clickable card links
    function setupCardLinks() {
        const links = document.querySelectorAll('a[data-card], a[data-card-name]');
        links.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const name = link.dataset.card || link.dataset.cardName;
                openCardModal(name);
            });
        });

        // Also setup links with title containing card names
        document.querySelectorAll('a[title]').forEach(link => {
            const title = link.title || link.textContent;
            if (isCardName(title)) {
                link.dataset.cardName = title;
                link.style.cursor = 'pointer';
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    openCardModal(title);
                });
            }
        });
    }

    function isCardName(text) {
        if (!text) return false;
        // Heuristic: contains words, possibly with (X) or [type]
        return /^[A-Z]/.test(text) && text.length > 2;
    }

    // Setup image elements with card data
    function setupCardImages() {
        document.querySelectorAll('img[data-card]').forEach(img => {
            const name = img.dataset.card;
            const group = img.dataset.group;
            const advanced = img.dataset.advanced === 'true';

            img.dataset.loaded = 'true';
            loadCardImage(img, name, { group, advanced });
        });
    }

    async function loadCardImage(imgEl, name, options = {}) {
        const url = await getImageUrl(name, options);
        imgEl.src = url;
    }

    async function getImageUrl(name, options = {}) {
        let url = getCardImageUrl(name, options);

        // Check if image exists, fallback to card back
        if (!(await checkImage(url))) {
            url = getCardBackUrl(options.isCrypt);
        }
        return url;
    }

    // Open modal with card image
    async function openCardModal(name) {
        if (!modalImg) modalImg = modalEl.querySelector('img');

        const isCrypt = name.toLowerCase().includes('crypt') ||
            document.querySelector('.crypt-card') ||
            name.length < 15;
        const url = await getImageUrl(name, { isCrypt });

        modalImg.src = url;
        modalImg.alt = name;
        modalEl.classList.add('show');
    }

    // Export for manual use
    window.CardUtils = {
        getCardImageUrl,
        getCardBackUrl,
        getCardName,
        openCardModal,
        BASE_URL,
        CARD_BACK,
    };
})();