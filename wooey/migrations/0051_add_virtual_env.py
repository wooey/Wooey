# Generated by Django 3.2.23 on 2023-11-22 02:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("wooey", "0050_add_api_keys"),
    ]

    operations = [
        migrations.CreateModel(
            name="VirtualEnvironment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=25)),
                ("python_binary", models.CharField(max_length=1024)),
                ("requirements", models.TextField()),
                ("venv_directory", models.CharField(max_length=1024)),
            ],
            options={
                "verbose_name": "virtual environment",
                "verbose_name_plural": "virtual environments",
            },
        ),
        migrations.AddField(
            model_name="script",
            name="virtual_environment",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="wooey.virtualenvironment",
            ),
        ),
    ]
