# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-25 02:50
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("wooey", "0020_userfile_finalize"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="favorite",
            options={"verbose_name": "favorite", "verbose_name_plural": "favorites"},
        ),
        migrations.AlterModelOptions(
            name="script",
            options={"verbose_name": "script", "verbose_name_plural": "scripts"},
        ),
        migrations.AlterModelOptions(
            name="scriptgroup",
            options={
                "verbose_name": "script group",
                "verbose_name_plural": "script groups",
            },
        ),
        migrations.AlterModelOptions(
            name="scriptparameter",
            options={
                "verbose_name": "script parameter",
                "verbose_name_plural": "script parameters",
            },
        ),
        migrations.AlterModelOptions(
            name="scriptparametergroup",
            options={
                "verbose_name": "script parameter group",
                "verbose_name_plural": "script parameter groups",
            },
        ),
        migrations.AlterModelOptions(
            name="scriptparameters",
            options={"verbose_name": "script parameters"},
        ),
        migrations.AlterModelOptions(
            name="scriptversion",
            options={
                "verbose_name": "script version",
                "verbose_name_plural": "script versions",
            },
        ),
        migrations.AlterModelOptions(
            name="wooeyfile",
            options={
                "verbose_name": "wooey file",
                "verbose_name_plural": "wooey files",
            },
        ),
        migrations.AlterModelOptions(
            name="wooeyjob",
            options={"verbose_name": "wooey job", "verbose_name_plural": "wooey jobs"},
        ),
    ]
