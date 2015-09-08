# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wooey.models.mixins


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0008_short_param_admin'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScriptVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('script_version', models.CharField(default='1', help_text='The script version.', max_length=50, blank=True)),
                ('script_iteration', models.PositiveSmallIntegerField(default=1)),
                ('script_path', models.FileField(upload_to=b'')),
                ('default_version', models.BooleanField(default=False)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('modified_date', models.DateTimeField(auto_now=True)),
                ('script', models.ForeignKey(related_name='script_version_new', to='wooey.Script')),
            ],
            bases=(wooey.models.mixins.ModelDiffMixin, wooey.models.mixins.WooeyPy2Mixin, models.Model),
        ),
        migrations.AddField(
            model_name='scriptparameter',
            name='script_version',
            field=models.ForeignKey(null=True, to='wooey.ScriptVersion'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='scriptparametergroup',
            name='script_version',
            field=models.ForeignKey(null=True, to='wooey.ScriptVersion'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='wooeyjob',
            name='script_version',
            field=models.ForeignKey(null=True, to='wooey.ScriptVersion'),
            preserve_default=False,
        ),
    ]
