# Generated by Django 3.2.15 on 2022-08-03 22:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("wooey", "0044_change_script_parameter_choices_to_text"),
    ]

    operations = [
        migrations.AddField(
            model_name="scriptversion",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_script_version_set",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="scriptversion",
            name="modified_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="modified_script_version_set",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
