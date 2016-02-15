# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0014_wooeyjob_uuid_finalise'),
    ]

    operations = [
        migrations.AddField(
            model_name='scriptparameter',
            name='hidden',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='scriptparametergroup',
            name='hidden',
            field=models.BooleanField(default=False),
        ),
    ]
