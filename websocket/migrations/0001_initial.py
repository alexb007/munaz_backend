from django.db import migrations

SQL = """
CREATE OR REPLACE FUNCTION notify_table_changes()
RETURNS trigger AS $$
DECLARE
    payload json;
BEGIN
    payload = json_build_object(
        'table', TG_TABLE_NAME,
        'action', TG_OP,
        'record', row_to_json(NEW),
        'old_record', row_to_json(OLD),
        'schema', TG_TABLE_SCHEMA
    );

    PERFORM pg_notify('db_changes', payload::text);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.RunSQL(SQL),
    ]
