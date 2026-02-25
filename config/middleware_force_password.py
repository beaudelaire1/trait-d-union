"""Middleware pour forcer le changement de mot de passe à la première connexion."""
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class ForcePasswordChangeMiddleware(MiddlewareMixin):
    """Redirection vers /account/change-password/ si le client doit changer son mot de passe.
    
    Utilise `request.session['must_change_password']` pour décider.
    Après un POST réussi sur change-password, le flag est retiré de la session
    ET du profil client (must_change_password = False).
    """
    
    EXEMPT_URLS = [
        '/account/change-password/',
        '/account/logout/',
        '/api/',
        '/admin/',
        '/static/',
        '/media/',
    ]
    
    def process_request(self, request):
        """Rediriger vers change-password si nécessaire."""
        
        # Vérifier si l'utilisateur est authentifié
        if not request.user.is_authenticated:
            return None
        
        # Vérifier si le chemin est dans les exemptions
        for exempt_url in self.EXEMPT_URLS:
            if request.path.startswith(exempt_url):
                return None
        
        # Vérifier le flag en session
        if request.session.get('must_change_password', False):
            redirect_url = reverse('account_change_password')
            if request.path != redirect_url:
                return redirect(redirect_url)
        
        return None
    
    def process_response(self, request, response):
        """Après un changement de mot de passe réussi, retirer le flag."""
        change_password_url = reverse('account_change_password')
        
        if (
            request.method == 'POST'
            and request.path == change_password_url
            and response.status_code in (200, 302)
            and request.session.get('must_change_password', False)
        ):
            # Vérifier que c'est une redirection (succès allauth)
            if response.status_code == 302:
                # Retirer le flag de la session
                request.session.pop('must_change_password', None)
                request.session.pop('must_change_password_reason', None)
                
                # Retirer le flag persistant du profil client
                try:
                    profile = request.user.client_profile
                    if profile.must_change_password:
                        profile.must_change_password = False
                        profile.save(update_fields=['must_change_password'])
                except (AttributeError, Exception):
                    pass
        
        return response
