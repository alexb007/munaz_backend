from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import connection


class Command(BaseCommand):
    help = "Create PostgreSQL triggers for realtime-enabled models"

    def handle(self, *args, **options):
        cursor = connection.cursor()
        created = 0
        skipped = 0

        for model in apps.get_models():
            meta = model._meta

            if not meta.managed:
                skipped += 1
                continue

            if not getattr(model, "realtime", False):
                skipped += 1
                continue

            table = meta.db_table
            trigger_name = f"{table}_realtime_notify"

            self.stdout.write(f"⏳ Processing {table}")

            cursor.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_trigger WHERE tgname = '{trigger_name}'
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

            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created/verified: {created}, skipped: {skipped}"
        ))
