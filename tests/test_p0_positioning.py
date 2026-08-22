"""Non-regression tests for the commercial positioning and SEO P0."""

from django.test import TestCase
from django.urls import reverse

from apps.pages.views import FAQView, HomeView, MethodView, ServicesView


class P0PositioningTests(TestCase):
    """Keep business infrastructure as TUS's primary public category."""

    def test_positioned_templates_are_the_public_templates(self):
        self.assertEqual(HomeView.template_name, "pages/home_positioned.html")
        self.assertEqual(ServicesView.template_name, "pages/services_positioned.html")
        self.assertEqual(MethodView.template_name, "pages/method_positioned.html")
        self.assertEqual(FAQView.template_name, "pages/faq_positioned.html")

    def test_services_page_leads_with_business_infrastructure(self):
        response = self.client.get(reverse("pages:services"))
        self.assertEqual(response.status_code, 200)

        body = response.content.decode()
        primary = body.index("Infrastructure métier sur mesure")
        ecommerce = body.index("Système de vente en ligne")
        web = body.index("Présence web stratégique")

        self.assertLess(primary, ecommerce)
        self.assertLess(primary, web)
        self.assertIn("CRM", body)
        self.assertIn("mini-ERP", body)
        self.assertIn("automatis", body.lower())
        self.assertNotIn(
            "Création Site Internet & E-commerce Guyane, Martinique, Guadeloupe",
            body,
        )

    def test_global_structured_data_uses_same_offer_hierarchy(self):
        response = self.client.get(reverse("pages:services"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()

        self.assertNotIn("Studio Web Cayenne", body)
        self.assertIn("Infrastructure métier Guyane", body)
        self.assertIn("Solutions métier et architecture digitale", body)

        primary = body.index('"name": "Infrastructure métier sur mesure"')
        ecommerce = body.index('"name": "Système de vente en ligne"')
        web = body.index('"name": "Présence web stratégique"')
        self.assertLess(primary, ecommerce)
        self.assertLess(primary, web)

    def test_homepage_metadata_targets_business_software(self):
        response = self.client.get(reverse("pages:home"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()

        self.assertIn("Plateformes métier & automatisation en Guyane", body)
        self.assertIn("CRM, mini-ERP, portails clients", body)
        self.assertIn("logiciel métier sur mesure guyane", body)

    def test_method_is_about_business_system_delivery(self):
        response = self.client.get(reverse("pages:method"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()

        self.assertIn("Méthode projet — Plateformes métier & automatisation", body)
        self.assertIn("Cartographie des flux", body)
        self.assertIn("Règles métier", body)
        self.assertIn("Tests automatisés", body)
        self.assertNotIn("Création de Site Internet en Guyane", body)

    def test_faq_is_not_structured_as_a_web_agency_faq(self):
        response = self.client.get(reverse("pages:faq"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()

        self.assertIn("Que construit Trait d'Union Studio ?", body)
        self.assertIn("plateformes métier sur mesure", body)
        self.assertIn("Quelle différence avec un CRM ou un ERP standard ?", body)
        self.assertNotIn(
            "Tout ce que vous devez savoir sur la création de sites web",
            body,
        )
        self.assertNotIn("Render (Francfort", body)

    def test_chroniques_index_metadata_matches_broader_editorial_scope(self):
        response = self.client.get(reverse("chroniques:list"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()

        self.assertIn(
            "Chroniques TUS — Entreprise, pilotage & transformation numérique",
            body,
        )
        self.assertIn("transformation numérique", body)
        self.assertNotIn("Articles & Réflexions sur le Web en Guyane", body)
