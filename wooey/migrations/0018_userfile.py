# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import wooey.models.mixins


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0017_wooeyfile_generate_checksums'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filename', models.TextField()),
                ('job', models.ForeignKey(to='wooey.WooeyJob')),
                ('parameter', models.ForeignKey(blank=True, to='wooey.ScriptParameters', null=True)),
            ],
            bases=(wooey.models.mixins.WooeyPy2Mixin, models.Model),
        ),
        migrations.AddField(
            model_name='userfile',
            name='system_file',
            field=models.ForeignKey(to='wooey.WooeyFile'),
        ),
    ]
