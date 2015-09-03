# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0009_script_versioning_data_migration'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scriptparameter',
            name='script',
        ),
        migrations.RemoveField(
            model_name='scriptparametergroup',
            name='script',
        ),
        migrations.RemoveField(
            model_name='wooeyjob',
            name='script',
        ),
        migrations.RemoveField(
            model_name='script',
            name='script_path',
        ),
        migrations.RemoveField(
            model_name='script',
            name='script_version',
        ),
    ]
