# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0019_userfile_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='wooeyfile',
            name='job',
        ),
        migrations.RemoveField(
            model_name='wooeyfile',
            name='parameter',
        ),
    ]
