# Generated manually - Fix missing related_url column

from django.db import migrations, connection


def fix_columns(apps, schema_editor):
    """Add related_url and remove link if needed - database agnostic."""
    with connection.cursor() as cursor:
        # Get existing columns
        table_name = 'clients_clientnotification'
        
        # Get column names based on database backend
        if connection.vendor == 'postgresql':
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = %s
            """, [table_name])
        else:  # SQLite
            cursor.execute(f"PRAGMA table_info({table_name})")
        
        if connection.vendor == 'postgresql':
            columns = [row[0] for row in cursor.fetchall()]
        else:
            columns = [row[1] for row in cursor.fetchall()]
        
        # Add related_url if missing
        if 'related_url' not in columns:
            cursor.execute(f"""
                ALTER TABLE {table_name} 
                ADD COLUMN related_url VARCHAR(255) NOT NULL DEFAULT ''
            """)
        
        # Remove link if it exists
        if 'link' in columns:
            if connection.vendor == 'postgresql':
                cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN link")
            else:
                # SQLite doesn't support DROP COLUMN before 3.35, but we can ignore
                pass


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0004_remove_clientnotification_link_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_columns, migrations.RunPython.noop),
    ]
