# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2018-02-18 16:09
from __future__ import unicode_literals

from django.db import migrations


def update_checksums(apps, schema_editor):
    ScriptVersion = apps.get_model('wooey', 'ScriptVersion')
    from wooey.backend import utils
    for obj in ScriptVersion.objects.all():
        checksum = utils.get_checksum(obj.script_path.read())
        obj.checksum = checksum
        obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0033_add-script-checksum'),
    ]

    operations = [
        migrations.RunPython(update_checksums)
    ]
