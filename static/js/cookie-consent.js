/* ==============================================================================
   COOKIE-CONSENT.JS — RGPD Cookie Consent Banner
   ==============================================================================
   Extracted from cookie_consent.html inline <script> block for:
   - Elimination of unsafe-inline in CSP
   - Better cacheability (immutable static file)
   ============================================================================== */

(function () {
    'use strict';

    const COOKIE_NAME = 'tus_cookie_consent';
    const COOKIE_EXPIRY_DAYS = 395; // 13 mois — conformité CNIL

    // Cookie utilities
    function setCookie(name, value, days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = "expires=" + date.toUTCString();
        document.cookie = name + "=" + JSON.stringify(value) + ";" + expires + ";path=/;SameSite=Lax";
    }

    function getCookie(name) {
        const nameEQ = name + "=";
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let c = cookies[i].trim();
            if (c.indexOf(nameEQ) === 0) {
                try {
                    return JSON.parse(c.substring(nameEQ.length));
                } catch (e) {
                    return null;
                }
            }
        }
        return null;
    }

    // DOM elements
    const banner = document.getElementById('cookie-consent');
    const modal = document.getElementById('cookie-modal');
    const modalBackdrop = document.getElementById('cookie-modal-backdrop');
    const analyticsCheckbox = document.getElementById('cookie-analytics');

    // Focus trap helper
    const FOCUSABLE_SELECTOR = 'a[href], button, input, textarea, select, [tabindex]:not([tabindex="-1"])';
    let previousFocusEl = null;

    function showBanner() {
        if (banner) {
            banner.classList.remove('translate-y-full');
        }
    }

    function hideBanner() {
        if (banner) {
            banner.classList.add('translate-y-full');
        }
    }

    function showModal() {
        if (modal) {
            previousFocusEl = document.activeElement;
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';

            // Focus first focusable element in modal
            const firstFocusable = modal.querySelector(FOCUSABLE_SELECTOR);
            if (firstFocusable) firstFocusable.focus();
        }
    }

    function hideModal() {
        if (modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = '';

            // Restore focus to the element that triggered the modal
            if (previousFocusEl) {
                previousFocusEl.focus();
                previousFocusEl = null;
            }
        }
    }

    // Apply preferences (load GA dynamically if accepted)
    function applyPreferences(consent) {
        if (consent.analytics) {
            if (typeof window._tusLoadGA === 'function') {
                window._tusLoadGA();
            }
        }
    }

    // Save consent
    function saveConsent(analytics) {
        const consent = {
            essential: true,
            analytics: analytics,
            marketing: false,
            timestamp: new Date().toISOString()
        };
        setCookie(COOKIE_NAME, consent, COOKIE_EXPIRY_DAYS);
        applyPreferences(consent);
        hideBanner();
        hideModal();
    }

    // Init
    function init() {
        const existingConsent = getCookie(COOKIE_NAME);

        if (existingConsent) {
            applyPreferences(existingConsent);
        } else {
            setTimeout(showBanner, 1000);
        }

        // Event listeners
        const acceptBtn = document.getElementById('cookie-accept');
        const rejectBtn = document.getElementById('cookie-reject');
        const settingsBtn = document.getElementById('cookie-settings-btn');
        const closeModalBtn = document.getElementById('cookie-modal-close');
        const saveSettingsBtn = document.getElementById('cookie-save-settings');

        if (acceptBtn) {
            acceptBtn.addEventListener('click', () => saveConsent(true));
        }

        if (rejectBtn) {
            rejectBtn.addEventListener('click', () => saveConsent(false));
        }

        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => {
                hideBanner();
                showModal();
            });
        }

        if (closeModalBtn) {
            closeModalBtn.addEventListener('click', hideModal);
        }

        if (modalBackdrop) {
            modalBackdrop.addEventListener('click', hideModal);
        }

        if (saveSettingsBtn) {
            saveSettingsBtn.addEventListener('click', () => {
                const analyticsEnabled = analyticsCheckbox ? analyticsCheckbox.checked : false;
                saveConsent(analyticsEnabled);
            });
        }

        // Keyboard: Escape to close, Tab trap in modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal && !modal.classList.contains('hidden')) {
                hideModal();
                return;
            }

            // Focus trap for cookie modal
            if (e.key === 'Tab' && modal && !modal.classList.contains('hidden')) {
                const focusables = modal.querySelectorAll(FOCUSABLE_SELECTOR);
                if (focusables.length === 0) return;

                const first = focusables[0];
                const last = focusables[focusables.length - 1];

                if (e.shiftKey) {
                    if (document.activeElement === first) {
                        e.preventDefault();
                        last.focus();
                    }
                } else {
                    if (document.activeElement === last) {
                        e.preventDefault();
                        first.focus();
                    }
                }
            }
        });
    }

    // Launch on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Global API to reopen cookie settings
    window.openCookieSettings = function () {
        showModal();
    };
})();
