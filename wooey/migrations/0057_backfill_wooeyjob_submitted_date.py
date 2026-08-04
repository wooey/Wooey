from django.db import migrations
from django.db.models import F


def backfill_submitted_date(apps, schema_editor):
    WooeyJob = apps.get_model("wooey", "WooeyJob")
    WooeyJob.objects.filter(submitted_date__isnull=True).update(
        submitted_date=F("created_date")
    )


class Migration(migrations.Migration):
    dependencies = [
        ("wooey", "0056_add_wooeyjob_submission_fields"),
    ]

    operations = [
        migrations.RunPython(backfill_submitted_date, migrations.RunPython.noop),
    ]
