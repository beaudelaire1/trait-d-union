# Generated manually - Fix missing related_url column

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0004_remove_clientnotification_link_and_more'),
    ]

    operations = [
        # Add related_url column if it doesn't exist (PostgreSQL)
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'clients_clientnotification' 
                    AND column_name = 'related_url'
                ) THEN
                    ALTER TABLE clients_clientnotification 
                    ADD COLUMN related_url VARCHAR(255) DEFAULT '' NOT NULL;
                END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Remove link column if it still exists
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'clients_clientnotification' 
                    AND column_name = 'link'
                ) THEN
                    ALTER TABLE clients_clientnotification DROP COLUMN link;
                END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
