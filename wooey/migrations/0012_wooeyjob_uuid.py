# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0011_script_versioning_cleanup'),
    ]

    operations = [
        # Add the uuid field with unique=False for existing entries
        # due to a bug in migrations this will set all to the same uuid
        migrations.AddField(
            model_name='wooeyjob',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, unique=False, max_length=255),
        ),
    ]
