# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuid, os

def gen_uuid(apps, schema_editor):
    WooeyJob = apps.get_model('wooey', 'WooeyJob')
    for obj in WooeyJob.objects.all():
        obj.uuid = uuid.uuid4()
        obj.save()


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
        # Set the uuids for existing records
        migrations.RunPython(gen_uuid),
        # Set to unique=True 
        migrations.AlterField(
            model_name='wooeyjob',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, unique=True, max_length=255),
        ),
    ]

