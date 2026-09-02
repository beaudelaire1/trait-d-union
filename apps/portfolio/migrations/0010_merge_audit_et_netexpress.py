"""Réunit les deux 0009 arrivées en parallèle sur la branche de déploiement.

Les deux dépendaient de 0008 : le graphe avait deux feuilles et Django
refusait toute migration — donc aussi le déploiement et la suite de tests.
Cette migration ne porte aucune opération, elle ne fait que refermer le
graphe.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("portfolio", "0009_alter_project_audit_last_run_at_and_more"),
        ("portfolio", "0009_update_netexpress_four_portals"),
    ]

    operations = []
