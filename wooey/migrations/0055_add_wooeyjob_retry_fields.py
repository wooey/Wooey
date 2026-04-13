from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wooey", "0054_add_script_version_is_active"),
    ]

    operations = [
        migrations.AddField(
            model_name="wooeyjob",
            name="retry_count",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="wooeyjob",
            name="status",
            field=models.CharField(
                choices=[
                    ("completed", "Completed"),
                    ("deleted", "Deleted"),
                    ("FAILURE", "Failed"),
                    ("error", "Error"),
                    ("queued", "Queued"),
                    ("RETRY", "Retrying"),
                    ("running", "Running"),
                    ("submitted", "Submitted"),
                ],
                default="submitted",
                max_length=255,
            ),
        ),
    ]
