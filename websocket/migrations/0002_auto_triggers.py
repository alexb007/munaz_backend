from django.db import migrations
from django.apps import apps

def create_triggers(apps, schema_editor):
    connection = schema_editor.connection
    cursor = connection.cursor()

    for model in apps.get_models():
        if not model._meta.managed or not getattr(model, "realtime", False):
            continue

        table = model._meta.db_table
        trigger_name = f"{table}_notify"

        cursor.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_trigger
                WHERE tgname = '{trigger_name}'
            ) THEN
                CREATE TRIGGER {trigger_name}
                AFTER INSERT OR UPDATE OR DELETE
                ON {table}
                FOR EACH ROW
                EXECUTE FUNCTION notify_table_changes();
            END IF;
        END;
        $$;
        """)

def drop_triggers(apps, schema_editor):
    cursor = schema_editor.connection.cursor()

    for model in apps.get_models():
        table = model._meta.db_table
        trigger_name = f"{table}_notify"
        cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name} ON {table};")

class Migration(migrations.Migration):
    dependencies = [
        ("websocket", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_triggers, drop_triggers),
    ]
