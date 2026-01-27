# Generated manually to fix missing column
from django.db import migrations, models


def add_column_if_missing(apps, schema_editor):
    """Add related_url column if it doesn't exist."""
    from django.db import connection
    with connection.cursor() as cursor:
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'clients_clientnotification' 
            AND column_name = 'related_url'
        """)
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE clients_clientnotification 
                ADD COLUMN related_url VARCHAR(255) DEFAULT '' NOT NULL
            """)


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0002_clientnotification_projectactivity_projectcomment'),
    ]

    operations = [
        migrations.RunPython(add_column_if_missing, migrations.RunPython.noop),
    ]
