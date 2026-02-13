/* ═══════════════════════════════════════════════════════════════════════════
   TRAIT D'UNION STUDIO — Admin Premium JS
   Raccourcis clavier · Animations · UX premium
   ═══════════════════════════════════════════════════════════════════════════ */

(function () {
    'use strict';

    /* ── Keyboard shortcuts ──────────────────────────────────────────── */

    function focusAdminSearch() {
        var searchInput = document.querySelector('#changelist-search input[type="text"]');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }

    function toggleFilterPanel() {
        var filterPanel = document.querySelector('#changelist-filter');
        if (!filterPanel || window.innerWidth > 1024) return;

        var isHidden = filterPanel.style.display === 'none';
        filterPanel.style.display = isHidden ? '' : 'none';

        var toggleBtn = document.getElementById('toggle-admin-filters');
        if (toggleBtn) {
            toggleBtn.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
        }
    }

    document.addEventListener('keydown', function (event) {
        var activeTag = document.activeElement && document.activeElement.tagName;
        var inTypingField = activeTag === 'INPUT' || activeTag === 'TEXTAREA' || activeTag === 'SELECT';

        // "/" or Ctrl+K → focus search
        if (!inTypingField && event.key === '/') {
            event.preventDefault();
            focusAdminSearch();
        }
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
            event.preventDefault();
            focusAdminSearch();
        }

        // "N" → add new object
        if (!inTypingField && (event.key === 'n' || event.key === 'N')) {
            var addButton = document.querySelector('.object-tools .addlink');
            if (addButton) {
                event.preventDefault();
                window.location.href = addButton.href;
            }
        }

        // "Escape" → close mobile filter
        if (event.key === 'Escape') {
            var filterPanel = document.querySelector('#changelist-filter');
            if (filterPanel && window.innerWidth <= 1024) {
                filterPanel.style.display = 'none';
            }
        }
    });

    /* ── Mobile filter toggle ────────────────────────────────────────── */

    function initMobileFilterToggle() {
        var filterPanel = document.querySelector('#changelist-filter');
        var search = document.querySelector('#changelist-search');
        if (!filterPanel || !search || window.innerWidth > 1024) return;
        if (document.getElementById('toggle-admin-filters')) return;

        var button = document.createElement('button');
        button.type = 'button';
        button.id = 'toggle-admin-filters';
        button.className = 'btn btn-outline-light';
        button.innerHTML = '<i class="fas fa-filter" style="margin-right:6px;font-size:.78rem"></i> Filtres';
        button.setAttribute('aria-label', 'Afficher ou masquer les filtres');
        button.setAttribute('aria-expanded', 'false');
        button.addEventListener('click', toggleFilterPanel);

        search.appendChild(button);
        filterPanel.style.display = 'none';
    }

    /* ── Form submission state ───────────────────────────────────────── */

    function markSubmittingForm(form) {
        if (!form || form.classList.contains('is-submitting')) return;
        form.classList.add('is-submitting');

        // Re-enable after 8s safety (in case of errors)
        setTimeout(function () {
            form.classList.remove('is-submitting');
        }, 8000);
    }

    /* ── Stagger animation on changelist rows ────────────────────────── */

    function animateChangelistRows() {
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

        var rows = document.querySelectorAll('#result_list tbody tr');
        rows.forEach(function (row, index) {
            row.style.opacity = '0';
            row.style.transform = 'translateY(6px)';
            row.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            row.style.transitionDelay = Math.min(index * 25, 400) + 'ms';

            requestAnimationFrame(function () {
                row.style.opacity = '1';
                row.style.transform = 'translateY(0)';
            });
        });
    }

    /* ── Animate cards on dashboard ──────────────────────────────────── */

    function animateDashboardCards() {
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

        var cards = document.querySelectorAll('.content-wrapper .card, .content-wrapper .small-box, .content-wrapper .info-box, #content-main .module');
        cards.forEach(function (card, index) {
            card.style.opacity = '0';
            card.style.transform = 'translateY(10px)';
            card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            card.style.transitionDelay = Math.min(index * 60, 500) + 'ms';

            requestAnimationFrame(function () {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            });
        });
    }

    /* ── Active sidebar highlight ────────────────────────────────────── */

    function highlightActiveSidebar() {
        var currentPath = window.location.pathname;
        var sidebarLinks = document.querySelectorAll('.nav-sidebar .nav-link');

        sidebarLinks.forEach(function (link) {
            var href = link.getAttribute('href');
            if (!href || href === '#') return;

            if (currentPath.indexOf(href) === 0 && href.length > 1) {
                link.classList.add('active');
                var parentItem = link.closest('.nav-item');
                if (parentItem) {
                    var parentMenu = parentItem.closest('.nav-treeview');
                    if (parentMenu) {
                        var parentNavItem = parentMenu.closest('.nav-item');
                        if (parentNavItem) {
                            parentNavItem.classList.add('menu-open');
                            var parentLink = parentNavItem.querySelector(':scope > .nav-link');
                            if (parentLink) parentLink.classList.add('active');
                        }
                    }
                }
            }
        });
    }

    /* ── Keyboard shortcuts hint ─────────────────────────────────────── */

    function addSearchPlaceholderHint() {
        var searchInput = document.querySelector('#changelist-search input[type="text"]');
        if (searchInput) {
            if (!searchInput.getAttribute('aria-label')) {
                searchInput.setAttribute('aria-label', 'Recherche dans la liste admin');
            }
            var currentPlaceholder = searchInput.getAttribute('placeholder') || '';
            if (currentPlaceholder.indexOf('/') === -1) {
                searchInput.setAttribute('placeholder', currentPlaceholder ? currentPlaceholder + '  (/)' : 'Rechercher…  (/)');
            }
        }
    }

    /* ── Auto-dismiss messages ───────────────────────────────────────── */

    function autoHideMessages() {
        var messages = document.querySelectorAll('.messagelist li, .messages .alert');
        messages.forEach(function (msg) {
            setTimeout(function () {
                msg.style.transition = 'opacity 0.5s ease, transform 0.5s ease, max-height 0.5s ease';
                msg.style.opacity = '0';
                msg.style.transform = 'translateY(-8px)';
                msg.style.maxHeight = '0';
                msg.style.padding = '0';
                msg.style.margin = '0';
                msg.style.overflow = 'hidden';
                setTimeout(function () { msg.remove(); }, 550);
            }, 5000);
        });
    }

    /* ── Init ─────────────────────────────────────────────────────────── */

    document.addEventListener('DOMContentLoaded', function () {
        // Accessibility
        addSearchPlaceholderHint();

        // Form submission protection
        var forms = document.querySelectorAll('form');
        forms.forEach(function (form) {
            form.addEventListener('submit', function () {
                markSubmittingForm(form);
            });
        });

        // Mobile UX
        initMobileFilterToggle();

        // Animations
        animateChangelistRows();
        animateDashboardCards();

        // Sidebar
        highlightActiveSidebar();

        // Auto-dismiss messages after 5s
        autoHideMessages();
    });

    window.addEventListener('resize', function () {
        if (window.innerWidth > 1024) {
            var filterPanel = document.querySelector('#changelist-filter');
            if (filterPanel) {
                filterPanel.style.display = '';
            }
        }
    });
})();
