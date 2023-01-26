# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid

from django.db import migrations, models


def gen_uuid(apps, schema_editor):
    WooeyJob = apps.get_model('wooey', 'WooeyJob')
    for obj in WooeyJob.objects.all():
        obj.uuid = uuid.uuid4()
        obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0012_wooeyjob_uuid'),
    ]

    operations = [
        # Set the uuids for existing records
        migrations.RunPython(gen_uuid),
    ]
