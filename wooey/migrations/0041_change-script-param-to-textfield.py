# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2019-06-09 08:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("wooey", "0040_add-widget-class"),
    ]

    operations = [
        migrations.AlterField(
            model_name="scriptparameter",
            name="parser",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="wooey.ScriptParser"
            ),
        ),
        migrations.AlterField(
            model_name="scriptparameter",
            name="script_param",
            field=models.TextField(),
        ),
    ]
