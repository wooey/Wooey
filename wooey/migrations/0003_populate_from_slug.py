# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("wooey", "0002_remove_scriptparameter_output_path"),
    ]

    operations = [
        migrations.AlterField(
            model_name="script",
            name="slug",
            field=models.SlugField(unique=True, editable=False),
        ),
        migrations.AlterField(
            model_name="scriptgroup",
            name="slug",
            field=models.SlugField(unique=True, editable=False),
        ),
        migrations.AlterField(
            model_name="scriptparameter",
            name="slug",
            field=models.SlugField(unique=True, editable=False),
        ),
    ]
