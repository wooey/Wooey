# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

def gen_checksums(apps, schema_editor):
    WooeyFile = apps.get_model('wooey', 'WooeyFile')
    from ..backend.utils import get_checksum
    for obj in WooeyFile.objects.all():
        try:
            obj.checksum = get_checksum(path=obj.filepath.path)
            obj.save()
        except IOError:
            print(obj.filepath, 'not found')


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0016_wooeyfile_checksum'),
    ]

    operations = [
        migrations.RunPython(gen_checksums),
    ]
