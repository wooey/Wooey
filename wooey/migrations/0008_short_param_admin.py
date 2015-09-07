# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0007_script_documentation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scriptparameter',
            name='short_param',
            field=models.CharField(max_length=255, blank=True),
        ),
    ]
