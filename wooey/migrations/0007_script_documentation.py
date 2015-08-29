# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0006_script_group_defaults'),
    ]

    operations = [
        migrations.AddField(
            model_name='script',
            name='documentation',
            field=models.TextField(null=True, blank=True),
        ),
    ]
