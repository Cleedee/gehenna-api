/**
 * Gehenna Web — Main Application JavaScript
 *
 * Includes:
 * - Confirmation modal via data attributes (replaces confirm())
 * - Flash message toasts via Bootstrap
 * - Active navbar link highlighting
 * - Loading spinner on form submit buttons
 * - Card hover tooltip initialization
 */

(function () {
    'use strict';

    /* ------------------------------------------
       Confirmation Modal (data-confirm)
       ------------------------------------------ */

    function initConfirmModal() {
        const modalEl = document.getElementById('confirmModal');
        if (!modalEl) return;

        const modal = new bootstrap.Modal(modalEl);
        const bodyEl = document.getElementById('confirmModalBody');
        const btnEl = document.getElementById('confirmModalBtn');

        document.addEventListener('click', function (e) {
            const trigger = e.target.closest('[data-confirm]');
            if (!trigger) return;

            // If it's an anchor with a direct href, use that
            let url = trigger.getAttribute('data-confirm-url');
            if (!url && trigger.tagName === 'A') {
                url = trigger.getAttribute('href');
            }

            const message = trigger.getAttribute('data-confirm') || 'Are you sure?';
            const actionLabel = trigger.getAttribute('data-confirm-action') || 'Confirm';

            e.preventDefault();

            bodyEl.textContent = message;
            btnEl.textContent = actionLabel;
            btnEl.href = url || '#';

            // Style the button based on action
            btnEl.className = 'btn';
            const actionLower = actionLabel.toLowerCase();
            if (actionLower === 'delete' || actionLower === 'remove') {
                btnEl.classList.add('btn-danger');
            } else {
                btnEl.classList.add('btn-primary');
            }

            modal.show();
        });
    }

    /* ------------------------------------------
       Flash Toasts
       ------------------------------------------ */

    function initFlashToasts() {
        const container = document.getElementById('toast-container');
        if (!container) return;

        container.querySelectorAll('.toast').forEach(function (toastEl) {
            const toast = new bootstrap.Toast(toastEl, {
                autohide: true,
                delay: 5000
            });
            toast.show();
        });
    }

    /* ------------------------------------------
       Active Navbar Link
       ------------------------------------------ */

    function initActiveNav() {
        const currentPath = window.location.pathname;
        document.querySelectorAll('.navbar-nav .nav-link').forEach(function (link) {
            const href = link.getAttribute('href');
            if (href && href !== '#' && currentPath.startsWith(href)) {
                link.classList.add('active');
            }
        });
    }

    /* ------------------------------------------
       Loading Spinner on Form Submit
       - Auto-disables submit buttons and shows a spinner
       - Works on any form with .btn-loading or all forms
       ------------------------------------------ */

    function initFormLoading() {
        document.addEventListener('submit', function (e) {
            const form = e.target;
            // Only handle forms with submit buttons
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (!submitBtn) return;

            // Don't double-process
            if (submitBtn.disabled) return;

            // Save original text
            const originalHtml = submitBtn.innerHTML;

            // Prevent double submit
            submitBtn.disabled = true;

            // Add spinner
            const spinnerHtml = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>';
            if (submitBtn.tagName === 'BUTTON') {
                submitBtn.innerHTML = spinnerHtml + ' ' + submitBtn.textContent.trim();
            } else {
                // input[type=submit]
                submitBtn.value = '⏳ ' + submitBtn.value;
            }

            // Re-enable after 10s as safety net (in case of network failure)
            setTimeout(function () {
                if (submitBtn.disabled) {
                    submitBtn.disabled = false;
                    if (submitBtn.tagName === 'BUTTON') {
                        submitBtn.innerHTML = originalHtml;
                    } else {
                        submitBtn.value = originalHtml;
                    }
                }
            }, 10000);
        });
    }

    /* ------------------------------------------
       Init
       ------------------------------------------ */

    document.addEventListener('DOMContentLoaded', function () {
        initConfirmModal();
        initFlashToasts();
        initActiveNav();
        initFormLoading();
    });

})();
