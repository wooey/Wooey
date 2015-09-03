# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wooey.models.mixins


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0008_script_versioning'),
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
        migrations.RenameField(
            model_name='scriptversion',
            old_name='script_version_new',
            new_name='script_version',
        ),
    ]
