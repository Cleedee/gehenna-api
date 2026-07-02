/**
 * Gehenna Web — Simple API Cache
 *
 * Caches API responses in localStorage with TTL.
 * Used by autocomplete and other AJAX features.
 */

(function () {
    'use strict';

    const CACHE_PREFIX = 'gehenna_cache_';
    const DEFAULT_TTL_MS = 5 * 60 * 1000; // 5 minutes

    const Cache = {
        /** Get cached value. Returns null if missing or expired. */
        get: function (key) {
            try {
                const raw = localStorage.getItem(CACHE_PREFIX + key);
                if (!raw) return null;
                const entry = JSON.parse(raw);
                if (Date.now() > entry.expires) {
                    localStorage.removeItem(CACHE_PREFIX + key);
                    return null;
                }
                return entry.value;
            } catch (_) {
                return null;
            }
        },

        /** Set cached value with TTL in milliseconds. */
        set: function (key, value, ttl) {
            try {
                const expires = Date.now() + (ttl || DEFAULT_TTL_MS);
                localStorage.setItem(CACHE_PREFIX + key, JSON.stringify({ value: value, expires: expires }));
            } catch (_) {
                // localStorage may be full or disabled
            }
        },

        /** Remove a cached entry. */
        remove: function (key) {
            try {
                localStorage.removeItem(CACHE_PREFIX + key);
            } catch (_) {}
        },

        /** Clear all Gehenna cache entries. */
        clear: function () {
            try {
                const keys = Object.keys(localStorage);
                keys.forEach(function (k) {
                    if (k.startsWith(CACHE_PREFIX)) {
                        localStorage.removeItem(k);
                    }
                });
            } catch (_) {}
        },
    };

    if (typeof window !== 'undefined') {
        window.GehCache = Cache;
    }

})();
