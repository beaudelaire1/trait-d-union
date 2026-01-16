#!/usr/bin/env python
"""
Script de test pour vérifier la configuration Brevo.

Usage:
    python test_brevo_email.py [email_destinataire]
    
Exemples:
    python test_brevo_email.py  # Utilise ADMIN_EMAIL
    python test_brevo_email.py test@example.com
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.conf import settings


def test_brevo_configuration():
    """Vérifie que Brevo est correctement configuré."""
    print("=" * 60)
    print("TEST DE CONFIGURATION BREVO")
    print("=" * 60)
    
    api_key = getattr(settings, 'BREVO_API_KEY', '')
    
    if not api_key:
        print("❌ BREVO_API_KEY non définie dans les settings")
        print("   Ajoutez BREVO_API_KEY dans votre fichier .env")
        return False
    
    # Masquer la clé pour l'affichage
    masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 20 else "***"
    print(f"✅ BREVO_API_KEY configurée: {masked_key}")
    print(f"✅ DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'non défini')}")
    print(f"✅ DEFAULT_FROM_NAME: {getattr(settings, 'DEFAULT_FROM_NAME', 'non défini')}")
    
    return True


def test_brevo_connection():
    """Teste la connexion à l'API Brevo."""
    print("\n" + "-" * 60)
    print("TEST DE CONNEXION API BREVO")
    print("-" * 60)
    
    try:
        from core.services.email_backends import brevo_service
        
        if not brevo_service.is_configured():
            print("❌ Service Brevo non configuré")
            return False
        
        # Tester l'accès à l'API
        import sib_api_v3_sdk
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = settings.BREVO_API_KEY
        
        api_instance = sib_api_v3_sdk.AccountApi(sib_api_v3_sdk.ApiClient(configuration))
        account = api_instance.get_account()
        
        print(f"✅ Connexion réussie!")
        print(f"   Entreprise: {account.company_name}")
        print(f"   Email: {account.email}")
        print(f"   Plan: {account.plan[0].type if account.plan else 'N/A'}")
        
        return True
        
    except ImportError:
        print("❌ Package sib-api-v3-sdk non installé")
        print("   Exécutez: pip install sib-api-v3-sdk")
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False


def send_test_email(recipient: str):
    """Envoie un email de test."""
    print("\n" + "-" * 60)
    print("ENVOI D'UN EMAIL DE TEST")
    print("-" * 60)
    
    try:
        from core.services.email_backends import send_transactional_email
        
        html_content = """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">
                🎉 Test Brevo réussi !
            </h1>
            <p style="font-size: 16px; color: #555;">
                Félicitations ! Votre configuration Brevo fonctionne parfaitement.
            </p>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>Expéditeur:</strong> {from_email}</p>
                <p><strong>Destinataire:</strong> {recipient}</p>
                <p><strong>Environnement:</strong> {env}</p>
            </div>
            <p style="color: #888; font-size: 12px;">
                Cet email a été envoyé via l'API Brevo depuis Trait d'Union Studio.
            </p>
        </div>
        """.format(
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient=recipient,
            env="Production" if not settings.DEBUG else "Développement"
        )
        
        result = send_transactional_email(
            to_email=recipient,
            subject="[TEST] Configuration Brevo - Trait d'Union Studio",
            html_content=html_content,
            tags=['test', 'brevo-config']
        )
        
        if result.get('success'):
            print(f"✅ Email envoyé avec succès!")
            print(f"   Message ID: {result.get('message_id')}")
            print(f"   Destinataire: {recipient}")
            return True
        else:
            print(f"❌ Échec de l'envoi: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi: {e}")
        return False


def main():
    """Point d'entrée principal."""
    # Récupérer le destinataire depuis les arguments ou les settings
    recipient = sys.argv[1] if len(sys.argv) > 1 else getattr(settings, 'ADMIN_EMAIL', None)
    
    if not recipient:
        print("❌ Aucun destinataire spécifié")
        print("   Usage: python test_brevo_email.py email@example.com")
        print("   Ou définissez ADMIN_EMAIL dans votre .env")
        sys.exit(1)
    
    # Exécuter les tests
    config_ok = test_brevo_configuration()
    
    if config_ok:
        connection_ok = test_brevo_connection()
        
        if connection_ok:
            print(f"\n📧 Envoi d'un email de test à: {recipient}")
            confirm = input("Continuer? (o/n): ").lower().strip()
            
            if confirm in ('o', 'oui', 'y', 'yes'):
                send_test_email(recipient)
            else:
                print("Envoi annulé.")
    
    print("\n" + "=" * 60)
    print("FIN DES TESTS")
    print("=" * 60)


if __name__ == '__main__':
    main()
