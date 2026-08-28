"""Aligne l'étude de cas NetExpress sur les quatre portails réellement livrés."""

from django.db import migrations


FORWARD_SOLUTION = """Construire un système robuste avec une interface ultra simple pour un public non technique, tout en couvrant :

- devis + factures PDF (statuts, numérotation, export);
- planification opérationnelle via des tasks (programmation des chantiers);
- 4 portails distincts : administration / client / ouvrier / cabinet comptable.

Le quatrième espace prolonge la plateforme jusqu'au partenaire comptable : factures clients et fournisseurs, pièces et documents utiles sont disponibles dans un accès dédié, sans recréer une chaîne d'e-mails parallèle."""

FORWARD_RESULT = """Une plateforme unique qui remplace les fichiers éparpillés : moins d'oublis, plus de contrôle, une expérience client plus transparente et une continuité administrative jusqu'au cabinet comptable.

Les quatre espaces partagent le même référentiel, chacun avec la visibilité utile à son rôle — de la demande commerciale au terrain, puis aux pièces nécessaires au suivi comptable."""

FORWARD_ANALYSIS = """Comprendre les points de friction de la gestion via Office : dispersion de l'info, oublis d'interventions, absence de suivi partagé. Nous avons cadré les besoins des 4 portails (administration / client / ouvrier / cabinet comptable) et le flux cible : demande → devis → exécution → facture → mise à disposition des pièces utiles au cabinet.

L'enjeu n'était pas d'ajouter un écran, mais de préserver un même fil d'information entre l'entreprise, le terrain, le client et son partenaire comptable."""

REVERSE_SOLUTION = """Construire un système robuste avec une interface ultra simple pour un public non technique, tout en couvrant :

- devis + factures PDF (statuts, numérotation, export);
- planification opérationnelle via des tasks (programmation des chantiers);
- 3 portails distincts : admin / client / ouvrier."""

REVERSE_RESULT = """Une plateforme unique qui remplace les fichiers éparpillés : moins d'oublis, plus de contrôle, une expérience client plus transparente et une chaîne complète prospect → devis → facture → exécution."""

REVERSE_ANALYSIS = """Comprendre les points de friction de la gestion via Office : dispersion de l'info, oublis d'interventions, absence de suivi partagé. Nous avons cadré les besoins des 3 portails (admin / client / ouvrier) et le flux cible : demande → devis → exécution → facture."""


def _update(apps, *, solution, result, analysis):
    Project = apps.get_model("portfolio", "Project")
    StrategyPhase = apps.get_model("portfolio", "StrategyPhase")

    project = Project.objects.filter(slug="netexpress").first()
    if project is None:
        return

    project.solution = solution
    project.result = result
    project.save(update_fields=["solution", "result"])

    StrategyPhase.objects.filter(
        project_id=project.pk,
        title="Analyse & Exploration",
    ).update(description=analysis)


def forwards(apps, schema_editor):
    _update(
        apps,
        solution=FORWARD_SOLUTION,
        result=FORWARD_RESULT,
        analysis=FORWARD_ANALYSIS,
    )


def backwards(apps, schema_editor):
    _update(
        apps,
        solution=REVERSE_SOLUTION,
        result=REVERSE_RESULT,
        analysis=REVERSE_ANALYSIS,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("portfolio", "0008_project_audit_fields"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
