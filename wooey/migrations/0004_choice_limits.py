# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0003_populate_from_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scriptparameter',
            name='choice_limit',
            field=models.CharField(max_length=10, null=True, blank=True),
        ),
    ]
