/**
 * Card Hover Tooltip — Gehenna Web
 *
 * Shows a rich floating preview when hovering over .card-link elements.
 * Uses event delegation for reliability across all cards (crypt + library).
 * Images sourced from KRCG: https://static.krcg.org/
 */

(function () {
    'use strict';

    const BASE_URL = 'https://static.krcg.org/card/';
    const CARD_BACK = 'https://static.krcg.org/cardback';

    let tooltipEl = null;
    let tooltipInner = null;
    let hideTimeout = null;
    let currentLink = null;

    /* ------------------------------------------
       Public API
       ------------------------------------------ */

    const CardUtils = {
        getCardImageUrl: getCardImageUrl,
        getCardBackUrl: getCardBackUrl,
        setupCardLinks: setupCardLinks,
        BASE_URL: BASE_URL,
        CARD_BACK: CARD_BACK,
    };

    if (typeof window !== 'undefined') {
        window.CardUtils = CardUtils;
    }

    /* ------------------------------------------
       Init
       ------------------------------------------ */

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    /* ------------------------------------------
       Core
       ------------------------------------------ */

    function init() {
        createStyles();
        createTooltip();
        setupCardLinks();
    }

    function createStyles() {
        const css = [
            '.card-tooltip {',
            '  position: fixed; z-index: 9999; display: none; pointer-events: none;',
            '  background: #1a1a2e; border: 1px solid #3a3a5a; border-radius: 8px;',
            '  box-shadow: 0 8px 24px rgba(0,0,0,0.6); padding: 0;',
            '  min-width: 200px; max-width: 320px; overflow: hidden;',
            '}',
            '.card-tooltip.show { display: block; }',
            '.card-tooltip-img {',
            '  width: 100%; max-width: 260px; height: auto; display: block;',
            '  border-bottom: 1px solid #3a3a5a;',
            '}',
            '.card-tooltip-body { padding: 8px 10px; color: #e0e0e0; font-size: 0.78rem; line-height: 1.4; }',
            '.card-tooltip-name { font-weight: 700; font-size: 0.88rem; color: #fff; margin-bottom: 4px; }',
            '.card-tooltip-row { display: flex; gap: 6px; align-items: baseline; margin-bottom: 2px; }',
            '.card-tooltip-label { color: #888; flex-shrink: 0; min-width: 60px; }',
            '.card-tooltip-value { color: #ccc; }',
            '.card-tooltip-text {',
            '  margin-top: 4px; color: #aaa; font-size: 0.75rem; line-height: 1.35;',
            '  border-top: 1px solid #2a2a4a; padding-top: 4px; max-height: 60px; overflow: hidden;',
            '}',
        ].join('\n');

        const style = document.createElement('style');
        style.textContent = css;
        document.head.appendChild(style);
    }

    function createTooltip() {
        tooltipEl = document.createElement('div');
        tooltipEl.className = 'card-tooltip';
        tooltipEl.innerHTML = ''
            + '<img class="card-tooltip-img" alt="">'
            + '<div class="card-tooltip-body">'
            + '  <div class="card-tooltip-name"></div>'
            + '  <div class="card-tooltip-row"><span class="card-tooltip-label">Type</span><span class="card-tooltip-value card-tooltip-type"></span></div>'
            + '  <div class="card-tooltip-row"><span class="card-tooltip-label">Clan</span><span class="card-tooltip-value card-tooltip-clan"></span></div>'
            + '  <div class="card-tooltip-row"><span class="card-tooltip-label">Cost</span><span class="card-tooltip-value card-tooltip-cost"></span></div>'
            + '  <div class="card-tooltip-text card-tooltip-text-content"></div>'
            + '</div>';

        document.body.appendChild(tooltipEl);

        tooltipInner = {
            img: tooltipEl.querySelector('.card-tooltip-img'),
            name: tooltipEl.querySelector('.card-tooltip-name'),
            type: tooltipEl.querySelector('.card-tooltip-type'),
            clan: tooltipEl.querySelector('.card-tooltip-clan'),
            cost: tooltipEl.querySelector('.card-tooltip-cost'),
            text: tooltipEl.querySelector('.card-tooltip-text-content'),
        };
    }

    /* ------------------------------------------
       Image URL helpers
       ------------------------------------------ */

    function getCardImageUrl(name, group, advanced) {
        if (!name) return getCardBackUrl();

        var baseName = name.toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/[^a-z0-9]/g, '')
            .replace(/^(the|an?)\s*/, '');

        // Library cards don't have groups — use default
        var groupNum = (group && group !== 'None' && group !== '') ? group : '2';
        var url = BASE_URL + baseName + 'g' + groupNum + '.webp';

        if (advanced === true || advanced === 'true') {
            url = BASE_URL + baseName + 'g' + groupNum + 'adv.webp';
        }

        return url;
    }

    function getCardBackUrl() {
        return CARD_BACK + 'library.jpg';
    }

    /* ------------------------------------------
       Show / Hide tooltip
       ------------------------------------------ */

    function showTooltip(el) {
        clearTimeout(hideTimeout);
        currentLink = el;

        var cardName = el.dataset.cardName || '';
        var group = el.dataset.group;
        var advanced = el.dataset.advanced;

        // Image
        tooltipInner.img.src = getCardImageUrl(cardName, group, advanced);
        tooltipInner.img.alt = cardName;

        // Name
        tooltipInner.name.textContent = cardName || 'Unknown Card';

        // Details from data attributes
        tooltipInner.type.textContent = el.dataset.tipo || '—';
        tooltipInner.clan.textContent = el.dataset.clan || '—';
        tooltipInner.cost.textContent = el.dataset.cost || '—';

        // Text (if available)
        var cardText = el.dataset.text || '';
        if (cardText) {
            tooltipInner.text.textContent = cardText;
            tooltipInner.text.style.display = '';
        } else {
            tooltipInner.text.style.display = 'none';
        }

        // Position
        var rect = el.getBoundingClientRect();
        var left = rect.left + window.scrollX;
        var top = rect.bottom + window.scrollY + 5;

        if (left + 330 > window.innerWidth) {
            left = Math.max(5, window.innerWidth - 335);
        }
        if (top + 350 > window.innerHeight) {
            top = Math.max(5, rect.top + window.scrollY - 350);
        }

        tooltipEl.style.left = left + 'px';
        tooltipEl.style.top = top + 'px';
        tooltipEl.classList.add('show');
    }

    function hideTooltip() {
        hideTimeout = setTimeout(function () {
            tooltipEl.classList.remove('show');
            currentLink = null;
        }, 100);
    }

    /* ------------------------------------------
       Event delegation (replaces per-element listeners)
       ------------------------------------------ */

    function setupCardLinks() {
        // Remove any existing listeners to avoid duplicates
        document.removeEventListener('mouseover', onMouseOver);
        document.removeEventListener('mouseout', onMouseOut);

        // Add delegation listeners
        document.addEventListener('mouseover', onMouseOver);
        document.addEventListener('mouseout', onMouseOut);
    }

    function onMouseOver(e) {
        var link = e.target.closest('.card-link');
        if (!link) return;
        if (link === currentLink) return; // already showing

        showTooltip(link);
    }

    function onMouseOut(e) {
        var link = e.target.closest('.card-link');
        if (!link) return;

        // Check if we're moving to a child element
        var related = e.relatedTarget;
        if (related && link.contains(related)) return;

        hideTooltip();
    }

})();
