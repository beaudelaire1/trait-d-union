/**
 * Micro-interactions pour Trait d'Union Studio
 * Effets "Waouh" : Boutons magnétiques et cartes avec lueur (glow)
 */

document.addEventListener('DOMContentLoaded', () => {
    initMagneticButtons();
    initCardGlow();
});

// Ré-initialiser après un swap HTMX
document.body.addEventListener('htmx:afterSettle', () => {
    initMagneticButtons();
    initCardGlow();
});

/**
 * Boutons magnétiques : le bouton suit légèrement le curseur
 */
function initMagneticButtons() {
    const magneticElements = document.querySelectorAll('.btn-primary, .btn-magnetic');
    
    magneticElements.forEach(el => {
        // Éviter d'attacher plusieurs fois les événements
        if (el.dataset.magneticInit) return;
        el.dataset.magneticInit = 'true';

        el.addEventListener('mousemove', (e) => {
            const rect = el.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            
            // Force magnétique (plus le diviseur est grand, moins l'effet est fort)
            const xForce = x / 3;
            const yForce = y / 3;
            
            el.style.transform = `translate(${xForce}px, ${yForce}px)`;
            
            // Si le bouton a un texte à l'intérieur, on peut aussi le bouger légèrement
            const text = el.querySelector('span');
            if (text) {
                text.style.transform = `translate(${xForce / 2}px, ${yForce / 2}px)`;
            }
        });

        el.addEventListener('mouseleave', () => {
            el.style.transform = 'translate(0px, 0px)';
            const text = el.querySelector('span');
            if (text) {
                text.style.transform = 'translate(0px, 0px)';
            }
        });
    });
}

/**
 * Effet de lueur (glow) sur les cartes au survol
 */
function initCardGlow() {
    const cards = document.querySelectorAll('.card-interactive, .bento-item, .portfolio-card, .card-premium');
    
    cards.forEach(card => {
        if (card.dataset.glowInit) return;
        card.dataset.glowInit = 'true';

        // Ajouter la classe pour le style CSS
        card.classList.add('glow-effect');

        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            card.style.setProperty('--mouse-x', `${x}px`);
            card.style.setProperty('--mouse-y', `${y}px`);
        });
    });
}
