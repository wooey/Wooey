# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0010_script_versioning_data_migration'),
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
        migrations.AlterField(
            model_name='scriptversion',
            name='script',
            field=models.ForeignKey(related_name='script_version', to='wooey.Script'),
        ),
        migrations.AlterField(
            model_name='scriptparameter',
            name='script_version',
            field=models.ForeignKey(to='wooey.ScriptVersion'),
        ),
        migrations.AlterField(
            model_name='scriptparametergroup',
            name='script_version',
            field=models.ForeignKey(to='wooey.ScriptVersion'),
        ),
        migrations.AlterField(
            model_name='wooeyjob',
            name='script_version',
            field=models.ForeignKey(to='wooey.ScriptVersion'),
        ),
    ]
