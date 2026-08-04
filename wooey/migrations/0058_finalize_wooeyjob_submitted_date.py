import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wooey", "0057_backfill_wooeyjob_submitted_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="wooeyjob",
            name="submitted_date",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
