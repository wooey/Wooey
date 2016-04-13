# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0015_hidden_parameters'),
    ]

    operations = [
        migrations.AddField(
            model_name='wooeyfile',
            name='checksum',
            field=models.CharField(max_length=40, blank=True),
        ),
    ]
