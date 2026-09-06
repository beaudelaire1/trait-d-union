"""Tests for the portfolio app."""
from django.test import TestCase, Client
from django.urls import reverse

from apps.portfolio.models import Project, ProjectType
from apps.portfolio.templatetags.portfolio_tags import safe_html_filter


class ProjectModelTest(TestCase):
    """Test the Project model."""

    def test_project_creation(self):
        """Test creating a project."""
        project = Project.objects.create(
            title="Site E-commerce Luxe",
            slug="site-ecommerce-luxe",
            project_type=ProjectType.COMMERCE,
            objective="Créer une boutique en ligne premium",
            solution="Développement sur mesure avec Django",
            result="Augmentation des ventes de 150%",
        )
        self.assertEqual(project.title, "Site E-commerce Luxe")
        self.assertEqual(project.project_type, ProjectType.COMMERCE)
        self.assertTrue(project.is_published)

    def test_project_str(self):
        """Test string representation."""
        project = Project.objects.create(
            title="Test Project",
            slug="test-project",
            project_type=ProjectType.SITE,
            objective="Test",
            solution="Test",
            result="Test",
        )
        self.assertEqual(str(project), "Test Project")

    def test_get_absolute_url(self):
        """Test the absolute URL generation."""
        project = Project.objects.create(
            title="URL Test",
            slug="url-test",
            project_type=ProjectType.OUTILS,
            objective="Test URL",
            solution="Test",
            result="Test",
        )
        expected_url = reverse('portfolio:detail', kwargs={'slug': 'url-test'})
        self.assertEqual(project.get_absolute_url(), expected_url)


class ProjectListViewTest(TestCase):
    """Test the portfolio list view."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('portfolio:list')
        # Create test projects
        self.project1 = Project.objects.create(
            title="Project 1",
            slug="project-1",
            project_type=ProjectType.SITE,
            objective="Objective 1",
            solution="Solution 1",
            result="Result 1",
            is_published=True,
        )
        self.project2 = Project.objects.create(
            title="Project 2",
            slug="project-2",
            project_type=ProjectType.COMMERCE,
            objective="Objective 2",
            solution="Solution 2",
            result="Result 2",
            is_published=True,
        )
        self.unpublished = Project.objects.create(
            title="Unpublished",
            slug="unpublished",
            project_type=ProjectType.OUTILS,
            objective="Hidden",
            solution="Hidden",
            result="Hidden",
            is_published=False,
        )

    def test_list_view_loads(self):
        """Test that the list view loads successfully."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portfolio/project_list.html')

    def test_only_published_projects_shown(self):
        """Test that only published projects are displayed."""
        response = self.client.get(self.url)
        projects = response.context['projects']
        self.assertEqual(projects.count(), 2)
        self.assertNotIn(self.unpublished, projects)

    def test_filter_by_type(self):
        """Test filtering projects by type."""
        response = self.client.get(self.url, {'type': 'site'})
        projects = response.context['projects']
        self.assertEqual(projects.count(), 1)
        self.assertEqual(projects[0], self.project1)

    def test_htmx_returns_partial(self):
        """Test that HTMX requests return the partial template."""
        response = self.client.get(
            self.url,
            HTTP_HX_REQUEST='true',
        )
        self.assertTemplateUsed(response, 'portfolio/_project_list_partial.html')


class ProjectDetailViewTest(TestCase):
    """Test the project detail view."""

    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(
            title="Detail Test",
            slug="detail-test",
            project_type=ProjectType.SITE,
            objective="Test objective",
            solution="Test solution",
            result="Test result",
            technologies=["Django", "Tailwind CSS", "HTMX"],
        )

    def test_detail_view_loads(self):
        """Test that the detail view loads."""
        url = reverse('portfolio:detail', kwargs={'slug': 'detail-test'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portfolio/project_detail.html')

    def test_project_in_context(self):
        """Test that the project is in context."""
        url = reverse('portfolio:detail', kwargs={'slug': 'detail-test'})
        response = self.client.get(url)
        self.assertEqual(response.context['project'], self.project)

    def test_404_for_invalid_slug(self):
        """Test that invalid slugs return 404."""
        url = reverse('portfolio:detail', kwargs={'slug': 'nonexistent'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class SafeHtmlFilterTest(TestCase):
    """Le filtre qui met en forme les textes des fiches.

    Une fiche saisie à la main dans l'admin arrive souvent en texte brut :
    ses paragraphes ne sont que des lignes vides. Sans mise en forme, la
    page les affiche d'un seul tenant, sans le moindre retour à la ligne.
    """

    def test_texte_brut_devient_des_paragraphes(self):
        """Les lignes vides d'un texte brut deviennent des paragraphes."""
        rendu = safe_html_filter("Premier bloc.\n\nDeuxième bloc.\n\nTroisième.")
        self.assertEqual(rendu.count("<p>"), 3)

    def test_html_deja_structure_reste_intact(self):
        """Un texte déjà balisé n'est pas remis en forme une seconde fois."""
        for source in ("<p>Un</p><p>Deux</p>", "<ul><li>Un</li></ul>", "Un<br>Deux"):
            with self.subTest(source=source):
                self.assertEqual(safe_html_filter(source), source)

    def test_le_gras_survit_a_la_mise_en_forme(self):
        """Les balises en ligne d'un texte brut sont conservées."""
        rendu = safe_html_filter("Du <strong>gras</strong>.\n\nUn second bloc.")
        self.assertIn("<strong>gras</strong>", rendu)
        self.assertEqual(rendu.count("<p>"), 2)

    def test_le_texte_brut_reste_assaini(self):
        """La mise en forme ne court-circuite pas l'assainissement."""
        rendu = safe_html_filter("Bonjour\n\n<script>alert(1)</script>\n\nAu revoir")
        self.assertNotIn("script", rendu)
        self.assertIn("Bonjour", rendu)
        self.assertIn("Au revoir", rendu)

    def test_valeur_vide(self):
        """Une valeur vide ne produit pas un paragraphe fantôme."""
        self.assertEqual(safe_html_filter(""), "")
        self.assertEqual(safe_html_filter(None), "")
