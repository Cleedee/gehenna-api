/**
 * Card Search Autocomplete — Gehenna Web
 *
 * Provides live suggestions when typing in the card name field.
 * Queries the API `/cards/` with debounce and shows a dropdown.
 */

(function () {
    'use strict';

    const API_BASE = window.GEHENNA_API_URL || 'http://127.0.0.1:8002';
    const DEBOUNCE_MS = 300;
    const MIN_CHARS = 2;
    const MAX_SUGGESTIONS = 12;

    let activeInput = null;
    let dropdownEl = null;
    let debounceTimer = null;
    let abortController = null;

    /* ------------------------------------------
       Init
       ------------------------------------------ */

    function init() {
        createDropdown();
        attachToInputs();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    /* ------------------------------------------
       Dropdown DOM
       ------------------------------------------ */

    function createDropdown() {
        if (dropdownEl) return;
        dropdownEl = document.createElement('div');
        dropdownEl.className = 'autocomplete-dropdown';
        dropdownEl.style.cssText = [
            'position: absolute',
            'z-index: 1050',
            'display: none',
            'background: var(--bg-surface, #16213e)',
            'border: 1px solid var(--border-muted, #3a3a5a)',
            'border-radius: 4px',
            'box-shadow: 0 4px 12px rgba(0,0,0,0.4)',
            'max-height: 360px',
            'overflow-y: auto',
            'min-width: 280px',
        ].join(';');
        dropdownEl.setAttribute('role', 'listbox');
        document.body.appendChild(dropdownEl);
    }

    /* ------------------------------------------
       Attach to card name inputs
       ------------------------------------------ */

    function attachToInputs() {
        document.querySelectorAll('input[name="name"]').forEach(function (input) {
            input.setAttribute('autocomplete', 'off');
            input.addEventListener('input', onInput);
            input.addEventListener('focus', onFocus);
            input.addEventListener('blur', onBlur);
            input.addEventListener('keydown', onKeydown);
        });
    }

    /* ------------------------------------------
       Event handlers
       ------------------------------------------ */

    function onInput(e) {
        const input = e.target;
        const value = input.value.trim();

        clearTimeout(debounceTimer);
        closeDropdown();

        if (value.length < MIN_CHARS) return;

        debounceTimer = setTimeout(function () {
            fetchSuggestions(input, value);
        }, DEBOUNCE_MS);
    }

    function onFocus(e) {
        activeInput = e.target;
        // Re-open if there's already a value
        const value = e.target.value.trim();
        if (value.length >= MIN_CHARS) {
            fetchSuggestions(e.target, value);
        }
    }

    function onBlur(e) {
        // Delay closing so click on dropdown registers
        setTimeout(function () {
            if (activeInput === e.target) {
                closeDropdown();
                activeInput = null;
            }
        }, 200);
    }

    function onKeydown(e) {
        if (!dropdownEl || dropdownEl.style.display === 'none') return;

        const items = dropdownEl.querySelectorAll('[role="option"]');
        if (!items.length) return;

        const activeItem = dropdownEl.querySelector('[role="option"].active') || items[0];
        let index = Array.from(items).indexOf(activeItem);

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                index = Math.min(index + 1, items.length - 1);
                setActiveItem(items[index]);
                scrollIntoView(items[index]);
                break;
            case 'ArrowUp':
                e.preventDefault();
                index = Math.max(index - 1, 0);
                setActiveItem(items[index]);
                scrollIntoView(items[index]);
                break;
            case 'Enter':
                e.preventDefault();
                if (activeItem) {
                    selectItem(activeItem);
                }
                break;
            case 'Escape':
                e.preventDefault();
                closeDropdown();
                break;
        }
    }

    /* ------------------------------------------
       API call
       ------------------------------------------ */

    function fetchSuggestions(input, query) {
        // Cancel previous request
        if (abortController) {
            abortController.abort();
        }
        abortController = new AbortController();

        // Check cache first
        const cacheKey = 'cards_search_' + query.toLowerCase();
        const cached = window.GehCache && window.GehCache.get(cacheKey);
        if (cached) {
            renderDropdown(input, cached);
            return;
        }

        const url = API_BASE + '/cards/?name=' + encodeURIComponent(query) + '&limit=' + MAX_SUGGESTIONS;

        fetch(url, {
            signal: abortController.signal,
            headers: {
                'Accept': 'application/json',
            }
        })
            .then(function (res) {
                if (!res.ok) throw new Error('HTTP ' + res.status);
                return res.json();
            })
            .then(function (data) {
                const cards = data.cards || [];
                // Cache for 2 minutes
                if (window.GehCache) {
                    window.GehCache.set(cacheKey, cards, 2 * 60 * 1000);
                }
                renderDropdown(input, cards);
            })
            .catch(function (err) {
                if (err.name === 'AbortError') return;
                console.warn('Autocomplete error:', err);
            });
    }

    /* ------------------------------------------
       Render dropdown
       ------------------------------------------ */

    function renderDropdown(input, cards) {
        if (!cards.length) {
            closeDropdown();
            return;
        }

        dropdownEl.innerHTML = '';
        dropdownEl.style.display = 'block';

        // Position below input
        const rect = input.getBoundingClientRect();
        dropdownEl.style.left = rect.left + window.scrollX + 'px';
        dropdownEl.style.top = rect.bottom + window.scrollY + 'px';
        dropdownEl.style.width = Math.max(rect.width, 280) + 'px';

        cards.forEach(function (card, idx) {
            const item = document.createElement('div');
            item.setAttribute('role', 'option');
            item.setAttribute('data-card-id', card.id);
            item.setAttribute('data-card-name', card.name);
            item.className = 'autocomplete-item';
            item.style.cssText = [
                'display: flex',
                'align-items: center',
                'gap: 8px',
                'padding: 8px 10px',
                'cursor: pointer',
                'border-bottom: 1px solid var(--border-subtle, #2a2a4a)',
                'transition: background 0.1s',
                'font-size: 0.85rem',
            ].join(';');
            if (idx === 0) item.classList.add('active');

            // Clan icon
            const clanIcon = card.clan_icon_url
                ? '<img src="' + card.clan_icon_url + '" alt="" style="width:16px;height:16px;flex-shrink:0;filter:brightness(0.85)">'
                : '';

            // Type badge
            const tipo = card.tipo ? '<span style="font-size:0.7rem;color:#888;margin-left:auto;flex-shrink:0">' + card.tipo + '</span>' : '';

            item.innerHTML = clanIcon + '<span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + escapeHtml(card.name) + '</span>' + tipo;

            item.addEventListener('mousedown', function (e) {
                e.preventDefault();
                selectItem(item);
            });

            item.addEventListener('mouseenter', function () {
                setActiveItem(item);
            });

            dropdownEl.appendChild(item);
        });
    }

    /* ------------------------------------------
       Selection
       ------------------------------------------ */

    function selectItem(item) {
        const cardId = item.getAttribute('data-card-id');
        const cardName = item.getAttribute('data-card-name');
        if (!cardId || !activeInput) return;

        // Fill the input and navigate to card detail
        activeInput.value = cardName;
        closeDropdown();

        // Navigate to card detail page
        window.location.href = '/cards/' + cardId;
    }

    /* ------------------------------------------
       Helpers
       ------------------------------------------ */

    function closeDropdown() {
        if (dropdownEl) {
            dropdownEl.style.display = 'none';
            dropdownEl.innerHTML = '';
        }
    }

    function setActiveItem(item) {
        dropdownEl.querySelectorAll('[role="option"]').forEach(function (el) {
            el.classList.remove('active');
            el.style.background = '';
        });
        if (item) {
            item.classList.add('active');
            item.style.background = 'var(--accent-light, rgba(233,69,96,0.15))';
        }
    }

    function scrollIntoView(item) {
        if (item && item.scrollIntoView) {
            item.scrollIntoView({ block: 'nearest' });
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    /* ------------------------------------------
       Public API
       ------------------------------------------ */

    window.CardAutocomplete = {
        init: init,
    };

})();
