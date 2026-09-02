"""Réunit les deux branches 0009 laissées ouvertes en parallèle.

`0009_alter_project_audit_last_run_at_and_more` (schéma) et
`0009_update_netexpress_four_portals` (données) dépendent toutes deux de
0008 : le graphe avait donc deux feuilles, et `manage.py migrate` s'arrêtait
sur « Conflicting migrations detected » — y compris au déploiement, où la
commande précède le démarrage de l'application.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("portfolio", "0009_alter_project_audit_last_run_at_and_more"),
        ("portfolio", "0009_update_netexpress_four_portals"),
    ]

    operations = []
