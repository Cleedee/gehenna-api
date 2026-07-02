/**
 * Gehenna Web — Theme Toggle (Dark/Light)
 *
 * Persists choice in localStorage.
 * Respects prefers-color-scheme as default.
 */

(function () {
    'use strict';

    const STORAGE_KEY = 'gehenna_theme';
    const THEME_DARK = 'dark';
    const THEME_LIGHT = 'light';

    function getPreferredTheme() {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored === THEME_DARK || stored === THEME_LIGHT) {
            return stored;
        }
        // Respect OS preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
            return THEME_LIGHT;
        }
        return THEME_DARK;
    }

    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme === THEME_LIGHT ? 'light' : 'dark');
        localStorage.setItem(STORAGE_KEY, theme);

        // Update toggle button icon
        const btn = document.getElementById('themeToggle');
        if (btn) {
            btn.innerHTML = theme === THEME_LIGHT
                ? '<span title="Switch to dark mode">&#9790;</span>'  // crescent moon
                : '<span title="Switch to light mode">&#9728;</span>'; // sun
            btn.setAttribute('aria-label', theme === THEME_LIGHT
                ? 'Switch to dark mode'
                : 'Switch to light mode');
        }
    }

    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme') || 'dark';
        const next = current === 'dark' ? THEME_LIGHT : THEME_DARK;
        setTheme(next);
    }

    function init() {
        // Create toggle button if not exists
        const navbar = document.querySelector('.navbar .navbar-nav:last-child');
        if (navbar && !document.getElementById('themeToggle')) {
            const li = document.createElement('li');
            li.className = 'nav-item';
            li.innerHTML = '<button id="themeToggle" class="nav-link btn btn-link border-0" aria-label="Switch theme"></button>';
            navbar.appendChild(li);
        }

        // Apply theme
        setTheme(getPreferredTheme());

        // Listen for OS theme changes
        if (window.matchMedia) {
            const mq = window.matchMedia('(prefers-color-scheme: light)');
            mq.addEventListener('change', function () {
                // Only change if user hasn't explicitly set a preference
                if (!localStorage.getItem(STORAGE_KEY)) {
                    setTheme(mq.matches ? THEME_LIGHT : THEME_DARK);
                }
            });
        }

        // Toggle on click
        document.addEventListener('click', function (e) {
            const btn = e.target.closest('#themeToggle');
            if (btn) {
                e.preventDefault();
                toggleTheme();
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
