// Card Hover functionality for Gehenna Web
// Based on KRCG: https://static.krcg.org/

(function () {
    'use strict';

    const BASE_URL = 'https://static.krcg.org/card/';
    const CARD_BACK = 'https://static.krcg.org/cardback';

    let tooltipEl = null;
    let tooltipImg = null;
    let hideTimeout = null;

    document.addEventListener('DOMContentLoaded', init);

    function init() {
        createStyles();
        createTooltip();
        setupCardLinks();
    }

    function createStyles() {
        const css = `
            .card-tooltip {
                position: fixed;
                z-index: 9999;
                display: none;
                pointer-events: none;
                background: white;
                padding: 5px;
                border-radius: 4px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }
            .card-tooltip img {
                width: 180px;
                height: auto;
                display: block;
            }
            .card-tooltip.show {
                display: block;
            }
        `;
        const style = document.createElement('style');
        style.textContent = css;
        document.head.appendChild(style);
    }

    function createTooltip() {
        tooltipEl = document.createElement('div');
        tooltipEl.className = 'card-tooltip';
        tooltipImg = document.createElement('img');
        tooltipEl.appendChild(tooltipImg);
        document.body.appendChild(tooltipEl);
    }

    function getCardImageUrl(name, group, advanced) {
        if (!name) return getCardBackUrl();

        let baseName = name.toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/[^a-z0-9]/g, '')
            .replace(/^(the|an?)\s*/, '');

        let groupNum = group || '2';
        let url = BASE_URL + baseName + 'g' + groupNum + '.webp';

        if (advanced === true || advanced === 'true') {
            url = BASE_URL + baseName + 'g' + groupNum + 'adv.webp';
        }

        return url;
    }

    function getCardBackUrl() {
        return CARD_BACK + 'library.jpg';
    }

    function showTooltip(el, cardName, group, advanced) {
        clearTimeout(hideTimeout);

        const url = getCardImageUrl(cardName, group, advanced);
        tooltipImg.src = url;
        tooltipImg.alt = cardName;

        const rect = el.getBoundingClientRect();
        let left = rect.left + window.scrollX;
        let top = rect.bottom + window.scrollY + 5;

        // Adjust if off screen
        if (left + 190 > window.innerWidth) {
            left = window.innerWidth - 195;
        }
        if (top + 250 > window.innerHeight) {
            top = rect.top + window.scrollY - 260;
        }

        tooltipEl.style.left = left + 'px';
        tooltipEl.style.top = top + 'px';
        tooltipEl.classList.add('show');
    }

    function hideTooltip() {
        hideTimeout = setTimeout(() => {
            tooltipEl.classList.remove('show');
        }, 100);
    }

    function setupCardLinks() {
        document.querySelectorAll('.card-link').forEach(link => {
            const cardName = link.dataset.cardName;
            const group = link.dataset.group;
            const advanced = link.dataset.advanced;

            link.addEventListener('mouseenter', (e) => {
                showTooltip(e.target, cardName, group, advanced);
            });

            link.addEventListener('mouseleave', hideTooltip);
        });
    }

    window.CardUtils = {
        getCardImageUrl,
        getCardBackUrl,
        BASE_URL,
        CARD_BACK,
    };
})();