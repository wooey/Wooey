from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wooey", "0053_add_script_audit_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="scriptversion",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
