# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2018-02-18 09:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wooey", "0032_rename-new-sv"),
    ]

    operations = [
        migrations.AddField(
            model_name="scriptversion",
            name="checksum",
            field=models.CharField(blank=True, max_length=40),
        ),
    ]
