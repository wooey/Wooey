# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-03 09:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wooey", "0026_rename_script_parameter_sv"),
    ]

    operations = [
        migrations.AddField(
            model_name="scriptparameter",
            name="param_order",
            field=models.SmallIntegerField(
                default=0, verbose_name="The order the parameter appears to the user."
            ),
        ),
        migrations.AlterField(
            model_name="scriptparameter",
            name="script_version",
            field=models.ManyToManyField(to="wooey.ScriptVersion"),
        ),
    ]
