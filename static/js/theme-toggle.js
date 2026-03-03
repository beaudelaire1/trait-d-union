/**
 * Theme Toggle — Trait d'Union Studio
 * Gère le passage entre dark mode (défaut) et light mode.
 * Persiste le choix via localStorage.
 * Supporte plusieurs boutons toggle (desktop + mobile).
 */
(function () {
    'use strict';

    const STORAGE_KEY = 'tus-theme';
    const LIGHT = 'light';
    const DARK = 'dark';

    /**
     * Applique le thème sur <html> et met à jour toutes les icônes toggle.
     * @param {'dark'|'light'} theme
     */
    function applyTheme(theme) {
        const root = document.documentElement;
        if (theme === LIGHT) {
            root.setAttribute('data-theme', LIGHT);
        } else {
            root.removeAttribute('data-theme');
        }
        updateAllToggleIcons(theme);
    }

    /**
     * Met à jour les icônes soleil/lune sur TOUS les boutons toggle.
     */
    function updateAllToggleIcons(theme) {
        // Toutes les icônes soleil et lune (class-based, pas id-based)
        var suns = document.querySelectorAll('.theme-icon-sun');
        var moons = document.querySelectorAll('.theme-icon-moon');
        var thumbs = document.querySelectorAll('.theme-toggle-thumb');

        suns.forEach(function(s) {
            if (theme === LIGHT) { s.classList.add('hidden'); } else { s.classList.remove('hidden'); }
        });
        moons.forEach(function(m) {
            if (theme === LIGHT) { m.classList.remove('hidden'); } else { m.classList.add('hidden'); }
        });
        // Déplace le thumb (pill toggle)
        thumbs.forEach(function(t) {
            if (theme === LIGHT) {
                t.classList.add('translate-x-5');
            } else {
                t.classList.remove('translate-x-5');
            }
        });
    }

    /**
     * Toggle entre dark et light.
     */
    function toggleTheme() {
        var current = localStorage.getItem(STORAGE_KEY) || DARK;
        var next = current === DARK ? LIGHT : DARK;
        localStorage.setItem(STORAGE_KEY, next);
        applyTheme(next);
    }

    // ── Initialisation immédiate (avant DOMContentLoaded pour éviter le FOUC) ──
    var saved = localStorage.getItem(STORAGE_KEY) || DARK;
    applyTheme(saved);

    // ── Bind de tous les boutons toggle après chargement du DOM ──
    document.addEventListener('DOMContentLoaded', function () {
        applyTheme(saved); // re-apply pour les icônes

        var btns = document.querySelectorAll('#theme-toggle-btn, #theme-toggle-btn-mobile');
        btns.forEach(function(btn) {
            btn.addEventListener('click', toggleTheme);
        });
    });
})();
