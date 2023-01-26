# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0013_wooeyjob_uuid_populate'),
    ]

    operations = [
        # Set to unique=True
        migrations.AlterField(
            model_name='wooeyjob',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, unique=True, max_length=255),
        ),
    ]
