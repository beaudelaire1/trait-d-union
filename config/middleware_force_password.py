"""Middleware pour forcer le changement de mot de passe à la première connexion."""
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class ForcePasswordChangeMiddleware(MiddlewareMixin):
    """Redirige OBLIGATOIREMENT vers /accounts/password/change/ si le client
    doit changer son mot de passe.

    Le client ne peut accéder à AUCUNE page du site tant qu'il n'a pas
    changé son mot de passe. Seules les pages exemptées (changement de
    mot de passe, logout, admin, static, media) sont accessibles.

    Utilise `request.session['must_change_password']` (posé au login
    via le signal allauth). Le flag est retiré après un POST réussi
    sur la page de changement de mot de passe.
    """

    # URLs exemptées du blocage (préfixes)
    EXEMPT_PREFIXES = [
        '/tus-gestion-secure/',
        '/static/',
        '/media/',
    ]

    def _get_change_password_url(self):
        """URL résolue dynamiquement via reverse (allauth)."""
        try:
            return reverse('account_change_password')
        except Exception:
            return '/accounts/password/change/'

    def process_request(self, request):
        # Utilisateur non authentifié → rien à faire
        if not request.user.is_authenticated:
            return None

        # Pas de flag → rien à faire
        if not request.session.get('must_change_password', False):
            return None

        # Vérifier les préfixes exemptés (admin, static, etc.)
        for prefix in self.EXEMPT_PREFIXES:
            if request.path.startswith(prefix):
                return None

        change_url = self._get_change_password_url()
        logout_url = reverse('account_logout')

        # Autoriser la page de changement de mot de passe et le logout
        if request.path in (change_url, logout_url):
            return None

        # TOUT LE RESTE est bloqué → redirection forcée
        return redirect(change_url)

    def process_response(self, request, response):
        """Après un changement de mot de passe réussi, retirer le flag.

        🛡️ BANK-GRADE: Vérifie directement le flag DB du profil client
        au lieu de se fier uniquement au code HTTP 302 (fragile si allauth
        change son comportement de redirection).
        """
        change_url = self._get_change_password_url()

        if (
            request.method == 'POST'
            and request.path == change_url
            and request.session.get('must_change_password', False)
        ):
            # Vérifier si le profil DB a été mis à jour (password réellement changé)
            # On accepte aussi le 302 comme signal complémentaire
            profile_cleared = False
            try:
                profile = request.user.client_profile
                # Recharger depuis la DB pour avoir l'état frais
                profile.refresh_from_db(fields=['must_change_password'])
                if not profile.must_change_password:
                    profile_cleared = True
            except (AttributeError, Exception):
                pass

            # Accepter si le profil DB est déjà clear OU si POST+302 (rétrocompat)
            if profile_cleared or response.status_code == 302:
                # Retirer le flag session
                request.session.pop('must_change_password', None)
                request.session.pop('must_change_password_reason', None)

                # S'assurer que le flag DB est aussi retiré
                if not profile_cleared:
                    try:
                        profile = request.user.client_profile
                        if profile.must_change_password:
                            profile.must_change_password = False
                            profile.save(update_fields=['must_change_password'])
                    except (AttributeError, Exception):
                        pass

        return response
