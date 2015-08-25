# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0006_script_group_defaults'),
    ]

    operations = [
        migrations.AlterField(
            model_name='script',
            name='script_version',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='script',
            name='slug',
            field=autoslug.fields.AutoSlugField(populate_from='script_name', unique_with=('script_version',), editable=False),
        ),
    ]
