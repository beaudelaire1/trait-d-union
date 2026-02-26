/* ==============================================================================
   APP.JS — Trait d'Union Studio
   ==============================================================================
   Extracted from base.html inline <script> block for:
   - Better cacheability (immutable static file)
   - Elimination of unsafe-inline in CSP
   - Maintainability
   ============================================================================== */

document.addEventListener('DOMContentLoaded', function () {

    // ============================================
    // LENIS — Buttery smooth scroll
    // ============================================
    const lenis = new Lenis({
        duration: 1.2,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
        orientation: 'vertical',
        gestureOrientation: 'vertical',
        smoothWheel: true,
        wheelMultiplier: 0.8,
        touchMultiplier: 1.5,
    });

    function raf(time) {
        lenis.raf(time);
        requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);

    // Pause Lenis on modals / overlays
    window.lenisInstance = lenis;

    // ============================================
    // HTMX Configuration - Simplified
    // ============================================

    // Only enable boost for specific elements, not globally
    // This prevents issues with full page navigation

    // Loading indicator for HTMX requests
    document.body.addEventListener('htmx:beforeRequest', function (evt) {
        document.body.classList.add('htmx-request');
        const target = evt.detail.elt;
        if (target.tagName === 'A' || target.tagName === 'BUTTON') {
            target.style.opacity = '0.7';
            target.style.pointerEvents = 'none';
        }
    });

    document.body.addEventListener('htmx:afterRequest', function (evt) {
        document.body.classList.remove('htmx-request');
        evt.detail.elt.style.opacity = '';
        evt.detail.elt.style.pointerEvents = '';
    });

    // ============================================
    // MICRO-INTERACTIONS
    // ============================================

    // Smooth scroll to anchors
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // ============================================
    // IMMERSIVE SCROLL REVEAL SYSTEM
    // ============================================
    // Generic reveals (.reveal, .reveal-scale, .reveal-left, .reveal-right, .reveal-rotate, .reveal-clip)
    const revealElements = document.querySelectorAll('.reveal, .reveal-scale, .reveal-left, .reveal-right, .reveal-rotate, .reveal-clip');

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const delay = entry.target.style.transitionDelay || entry.target.style.animationDelay || '0s';
                const ms = parseFloat(delay) * 1000;
                setTimeout(() => entry.target.classList.add('active'), ms);
                revealObserver.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.08,
        rootMargin: '0px 0px -60px 0px'
    });

    revealElements.forEach(el => revealObserver.observe(el));

    // Suspense dividers — cinematic reveal with .active class
    const suspenseDividers = document.querySelectorAll('.suspense-divider');
    if (suspenseDividers.length > 0) {
        const dividerObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                    dividerObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.3, rootMargin: '0px 0px -80px 0px' });
        suspenseDividers.forEach(d => dividerObserver.observe(d));
    }

    // Stagger children containers
    const staggerElements = document.querySelectorAll('.stagger-children');
    const staggerObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                // Apply stagger delay to each child
                Array.from(entry.target.children).forEach((child, i) => {
                    child.style.transitionDelay = `${i * 0.12}s`;
                });
                staggerObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    staggerElements.forEach(el => staggerObserver.observe(el));

    // ============================================
    // METHOD PAGE — Timeline Step-by-Step Reveal
    // ============================================
    const methodSteps = document.querySelectorAll('.method-step');
    const timelineProgress = document.getElementById('timeline-progress');

    if (methodSteps.length > 0) {
        // Timeline progress bar driven by scroll
        if (timelineProgress) {
            const timeline = document.getElementById('method-timeline');
            window.addEventListener('scroll', () => {
                if (!timeline) return;
                const rect = timeline.getBoundingClientRect();
                const totalHeight = rect.height;
                const scrolled = Math.max(0, -rect.top + window.innerHeight * 0.5);
                const progress = Math.min(1, scrolled / totalHeight);
                timelineProgress.style.transform = `scaleY(${progress})`;
                timelineProgress.style.transformOrigin = 'top';
            }, { passive: true });
        }

        // Each step reveals individually
        const stepObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const step = entry.target;
                    const number = step.querySelector('.step-number');
                    const content = step.querySelector('.step-reveal');

                    // 1) Number pops in
                    if (number) {
                        setTimeout(() => number.classList.add('active'), 100);
                    }
                    // 2) Content slides in after number
                    if (content) {
                        setTimeout(() => content.classList.add('active'), 350);
                    }

                    stepObserver.unobserve(step);
                }
            });
        }, { threshold: 0.2, rootMargin: '0px 0px -80px 0px' });

        methodSteps.forEach(step => stepObserver.observe(step));
    }

    // ============================================
    // NAVBAR SCROLL EFFECT
    // ============================================
    const navbar = document.getElementById('navbar');
    let lastScroll = 0;

    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;

        if (currentScroll > 50) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }

        lastScroll = currentScroll;
    }, { passive: true });

    // ============================================
    // IMMERSIVE CUSTOM CURSOR — hides OS cursor
    // ============================================
    if (window.matchMedia('(hover: hover) and (min-width: 1024px)').matches && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        // Hide OS cursor globally
        document.documentElement.classList.add('has-custom-cursor');

        const cursorDot = document.createElement('div');
        const cursorRing = document.createElement('div');
        cursorDot.className = 'cursor-dot';
        cursorRing.className = 'cursor-ring';
        document.body.appendChild(cursorDot);
        document.body.appendChild(cursorRing);

        let mouseX = -100, mouseY = -100;
        let ringX = -100, ringY = -100;
        let isVisible = false;

        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
            cursorDot.style.left = mouseX + 'px';
            cursorDot.style.top = mouseY + 'px';
            if (!isVisible) {
                cursorDot.style.opacity = '1';
                cursorRing.style.opacity = '1';
                isVisible = true;
            }
        });

        // Hide cursor when leaving the window
        document.addEventListener('mouseleave', () => {
            cursorDot.style.opacity = '0';
            cursorRing.style.opacity = '0';
            isVisible = false;
        });

        // Smooth ring follow with lerp
        function animateRing() {
            ringX += (mouseX - ringX) * 0.12;
            ringY += (mouseY - ringY) * 0.12;
            cursorRing.style.left = ringX + 'px';
            cursorRing.style.top = ringY + 'px';
            requestAnimationFrame(animateRing);
        }
        animateRing();

        // Click feedback
        document.addEventListener('mousedown', () => {
            cursorDot.classList.add('clicking');
            cursorRing.classList.add('clicking');
        });
        document.addEventListener('mouseup', () => {
            cursorDot.classList.remove('clicking');
            cursorRing.classList.remove('clicking');
        });

        // Dynamic hover states
        function addCursorHovers() {
            // Standard interactive elements → ring grows
            document.querySelectorAll('a, button, .card-premium, .bento-item, input, textarea, select, .card-interactive, .faq-item').forEach(el => {
                el.addEventListener('mouseenter', () => {
                    cursorRing.classList.remove('hover-text');
                    cursorRing.classList.add('hover');
                });
                el.addEventListener('mouseleave', () => {
                    cursorRing.classList.remove('hover', 'hover-text');
                });
            });
            // Portfolio/case-study cards → ring becomes "Voir" button
            document.querySelectorAll('[data-cursor="view"], .portfolio-card, .case-study-card').forEach(el => {
                el.addEventListener('mouseenter', () => {
                    cursorRing.classList.remove('hover');
                    cursorRing.classList.add('hover-text');
                });
                el.addEventListener('mouseleave', () => {
                    cursorRing.classList.remove('hover-text');
                });
            });
        }
        addCursorHovers();

        // Re-bind after HTMX swaps
        document.body.addEventListener('htmx:afterSwap', addCursorHovers);
    }

    // ============================================
    // HTMX AFTERSWAP — Re-init animations on dynamic content
    // ============================================
    document.body.addEventListener('htmx:afterSettle', function (evt) {
        const target = evt.detail.target || document.body;
        // Re-observe reveal elements inside swapped content
        target.querySelectorAll('.reveal, .reveal-scale, .reveal-left, .reveal-right, .reveal-rotate, .reveal-clip').forEach(el => {
            if (!el.classList.contains('active')) {
                revealObserver.observe(el);
            }
        });
        // Re-observe stagger containers
        target.querySelectorAll('.stagger-children').forEach(el => {
            if (!el.classList.contains('active')) {
                staggerObserver.observe(el);
            }
        });
        // Re-bind card tilt
        target.querySelectorAll('.card-tilt').forEach(card => {
            if (!card.dataset.tiltBound) {
                card.dataset.tiltBound = 'true';
                card.addEventListener('mousemove', function (e) {
                    const rect = card.getBoundingClientRect();
                    const x = (e.clientX - rect.left) / rect.width;
                    const y = (e.clientY - rect.top) / rect.height;
                    const rotateX = (0.5 - y) * 8;
                    const rotateY = (x - 0.5) * 8;
                    card.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
                });
                card.addEventListener('mouseleave', function () {
                    card.style.transform = 'perspective(800px) rotateX(0) rotateY(0)';
                });
            }
        });
    });

    // ============================================
    // BENTO CARD MOUSE GLOW EFFECT
    // ============================================
    document.querySelectorAll('.bento-item').forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;
            card.style.setProperty('--mouse-x', x + '%');
            card.style.setProperty('--mouse-y', y + '%');
        });
    });

    // ============================================
    // PARALLAX — Subtle depth on background blobs
    // ============================================
    const parallaxElements = document.querySelectorAll('.parallax-slow');
    if (parallaxElements.length > 0 && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        let ticking = false;
        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    const scrollY = window.pageYOffset;
                    parallaxElements.forEach(el => {
                        const speed = parseFloat(el.dataset.speed) || 0.3;
                        el.style.transform = `translateY(${scrollY * speed}px)`;
                    });
                    ticking = false;
                });
                ticking = true;
            }
        }, { passive: true });
    }

    // ============================================
    // CARD 3D TILT EFFECT — Premium hover
    // ============================================
    document.querySelectorAll('.card-tilt').forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width;
            const y = (e.clientY - rect.top) / rect.height;
            const tiltX = (0.5 - y) * 8;  // max 4deg
            const tiltY = (x - 0.5) * 8;
            card.style.transform = `perspective(800px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) translateZ(4px)`;
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(800px) rotateX(0) rotateY(0) translateZ(0)';
        });
    });

    // ============================================
    // NUMBER COUNTER ANIMATION
    // ============================================
    const counters = document.querySelectorAll('.counter');
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !entry.target.dataset.counted) {
                entry.target.dataset.counted = 'true';
                const target = parseInt(entry.target.dataset.target);
                const suffix = entry.target.dataset.suffix || '';
                let current = 0;
                const increment = target / 50;
                const timer = setInterval(() => {
                    current += increment;
                    if (current >= target) {
                        entry.target.textContent = target + suffix;
                        clearInterval(timer);
                    } else {
                        entry.target.textContent = Math.floor(current) + suffix;
                    }
                }, 30);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(c => counterObserver.observe(c));

    // ============================================
    // VALIDATION INLINE & ARIA LIVE ANNOUNCEMENTS
    // ============================================

    // Créer un conteneur d'annonces pour les lecteurs d'écran
    (function initializeAccessibility() {
        // Conteneur aria-live pour annonces dynamiques
        if (!document.getElementById('aria-announcer')) {
            const announcer = document.createElement('div');
            announcer.id = 'aria-announcer';
            announcer.className = 'sr-only-announce';
            announcer.setAttribute('aria-live', 'polite');
            announcer.setAttribute('aria-atomic', 'true');
            document.body.appendChild(announcer);
        }

        // Fonction d'annonce accessible
        window.announce = function (message, priority = 'polite') {
            const announcer = document.getElementById('aria-announcer');
            if (announcer) {
                announcer.setAttribute('aria-live', priority);
                announcer.textContent = '';
                setTimeout(() => {
                    announcer.textContent = message;
                }, 100);
            }
        };

        // Validation en temps réel pour les formulaires
        const forms = document.querySelectorAll('form:not(.no-validate)');
        forms.forEach(form => {
            // État de chargement lors de la soumission
            form.addEventListener('submit', function (e) {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn && !submitBtn.hasAttribute('data-no-loading')) {
                    submitBtn.setAttribute('disabled', 'true');
                    submitBtn.setAttribute('aria-busy', 'true');
                    const originalText = submitBtn.textContent;
                    submitBtn.dataset.originalText = originalText;

                    // Annonce pour lecteurs d'écran
                    window.announce('Envoi en cours, veuillez patienter', 'assertive');

                    // Restaurer après 30s maximum (sécurité)
                    setTimeout(() => {
                        if (submitBtn.hasAttribute('disabled')) {
                            submitBtn.removeAttribute('disabled');
                            submitBtn.removeAttribute('aria-busy');
                            submitBtn.textContent = submitBtn.dataset.originalText;
                        }
                    }, 30000);
                }
            });

            // Validation des inputs en temps réel
            const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
            inputs.forEach(input => {
                // Ajouter attribut aria-required
                input.setAttribute('aria-required', 'true');

                // Valider au blur
                input.addEventListener('blur', function () {
                    validateInput(this);
                });

                // Valider pendant la saisie (debounced)
                let timeout;
                input.addEventListener('input', function () {
                    clearTimeout(timeout);
                    timeout = setTimeout(() => {
                        if (this.value.length > 0) {
                            validateInput(this);
                        }
                    }, 500);
                });
            });
        });

        // Fonction de validation d'input
        function validateInput(input) {
            const value = input.value.trim();
            const type = input.type;
            let isValid = true;
            let message = '';

            // Validation selon le type
            if (input.hasAttribute('required') && !value) {
                isValid = false;
                message = 'Ce champ est requis';
            } else if (type === 'email' && value) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                isValid = emailRegex.test(value);
                message = isValid ? 'Email valide' : 'Format email invalide';
            } else if (type === 'tel' && value) {
                const telRegex = /^[\d\s\-\+\(\)]+$/;
                isValid = telRegex.test(value);
                message = isValid ? 'Numéro valide' : 'Format téléphone invalide';
            } else if (input.hasAttribute('minlength') && value) {
                const minLength = parseInt(input.getAttribute('minlength'));
                isValid = value.length >= minLength;
                message = isValid ? 'Longueur suffisante' : `Minimum ${minLength} caractères`;
            } else if (value) {
                isValid = true;
                message = 'Champ valide';
            }

            // Appliquer les classes visuelles
            input.classList.remove('valid', 'invalid');
            if (value) {
                input.classList.add(isValid ? 'valid' : 'invalid');
                input.setAttribute('aria-invalid', !isValid);
            }

            // Wrapper parent pour icône
            const wrapper = input.closest('.input-wrapper');
            if (wrapper && value) {
                wrapper.classList.remove('has-success', 'has-error');
                wrapper.classList.add(isValid ? 'has-success' : 'has-error');
            }

            // Afficher message si erreur
            let messageEl = input.parentElement.querySelector('.form-message');
            if (!isValid && value) {
                if (!messageEl) {
                    messageEl = document.createElement('div');
                    messageEl.className = 'form-message error';
                    messageEl.setAttribute('role', 'alert');
                    input.parentElement.appendChild(messageEl);
                }
                messageEl.innerHTML = `<span>⚠</span><span>${message}</span>`;
                messageEl.classList.remove('success');
                messageEl.classList.add('error');

                // Annonce pour lecteurs d'écran
                window.announce(`Erreur : ${message}`, 'assertive');
            } else if (messageEl) {
                messageEl.remove();
            }

            return isValid;
        }

        // Exposer la fonction globalement pour usage externe
        window.validateInput = validateInput;
    })();

    // ============================================
    // EMAIL OBFUSCATION (Anti-Spam Protection)
    // ============================================
    // Décode les emails encodés Base64 dans les liens .tus-email-link
    // Exécuté une seule fois au chargement de la page
    (function () {
        function decodeEmails() {
            const links = document.querySelectorAll('.tus-email-link[data-email]');
            links.forEach(link => {
                try {
                    const encoded = link.getAttribute('data-email');
                    const decoded = atob(encoded); // Décodage Base64
                    const label = link.getAttribute('data-label') || 'Nous écrire';
                    link.href = 'mailto:' + decoded;
                    link.textContent = label;
                    link.removeAttribute('data-email'); // Nettoyer après utilisation
                } catch (e) {
                    console.warn('⚠️ Erreur décodage email:', e);
                    link.textContent = 'Nous contacter';
                    link.href = '/contact/';
                }
            });
        }

        // Exécuter immédiatement
        decodeEmails();
    })();

}); // fin DOMContentLoaded
