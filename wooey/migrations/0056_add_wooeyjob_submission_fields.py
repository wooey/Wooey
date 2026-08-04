from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wooey", "0055_add_wooeyjob_retry_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="wooeyjob",
            name="submission_id",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name="wooeyjob",
            name="submitted_date",
            field=models.DateTimeField(null=True),
        ),
    ]
