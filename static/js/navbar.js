/* ==============================================================================
   NAVBAR.JS — Mobile Menu Toggle
   ==============================================================================
   Extracted from navbar.html inline <script> block for:
   - Elimination of unsafe-inline in CSP
   - Better cacheability (immutable static file)
   ============================================================================== */

document.addEventListener('DOMContentLoaded', function () {
    const menuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    const iconOpen = document.getElementById('menu-icon-open');
    const iconClose = document.getElementById('menu-icon-close');
    const navbarLogo = document.getElementById('navbar-logo');
    let isOpen = false;

    // All focusable elements inside the mobile menu
    const FOCUSABLE_SELECTOR = 'a[href], button, input, textarea, select, [tabindex]:not([tabindex="-1"])';

    if (menuBtn && mobileMenu) {
        menuBtn.addEventListener('click', function () {
            isOpen = !isOpen;

            if (isOpen) {
                // Open menu
                mobileMenu.classList.remove('translate-x-full', 'opacity-0');
                mobileMenu.classList.add('translate-x-0', 'opacity-100');
                iconOpen.classList.add('opacity-0', 'scale-0');
                iconClose.classList.remove('opacity-0', 'scale-0');
                menuBtn.setAttribute('aria-expanded', 'true');
                document.body.style.overflow = 'hidden';
                if (navbarLogo) navbarLogo.style.opacity = '0';

                // Focus trap: focus first link
                const firstFocusable = mobileMenu.querySelector(FOCUSABLE_SELECTOR);
                if (firstFocusable) firstFocusable.focus();
            } else {
                closeMenu();
            }
        });

        // Close menu on link click
        mobileMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', closeMenu);
        });

        // Focus trap: prevent tabbing outside the mobile menu
        document.addEventListener('keydown', function (e) {
            if (!isOpen) return;

            if (e.key === 'Escape') {
                closeMenu();
                menuBtn.focus();
                return;
            }

            if (e.key === 'Tab') {
                const focusables = [menuBtn, ...mobileMenu.querySelectorAll(FOCUSABLE_SELECTOR)];
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

    function closeMenu() {
        isOpen = false;
        if (mobileMenu) {
            mobileMenu.classList.add('translate-x-full', 'opacity-0');
            mobileMenu.classList.remove('translate-x-0', 'opacity-100');
        }
        if (iconOpen) iconOpen.classList.remove('opacity-0', 'scale-0');
        if (iconClose) iconClose.classList.add('opacity-0', 'scale-0');
        if (menuBtn) menuBtn.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
        if (navbarLogo) navbarLogo.style.opacity = '1';
    }
});
