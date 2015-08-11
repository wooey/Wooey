# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields
from django.conf import settings
import wooey.models.mixins


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WooeyFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filepath', models.FileField(max_length=500, upload_to=b'')),
                ('filepreview', models.TextField(null=True, blank=True)),
                ('filetype', models.CharField(max_length=255, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='WooeyJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('celery_id', models.CharField(max_length=255, null=True)),
                ('job_name', models.CharField(max_length=255)),
                ('job_description', models.TextField(null=True, blank=True)),
                ('stdout', models.TextField(null=True, blank=True)),
                ('stderr', models.TextField(null=True, blank=True)),
                ('status', models.CharField(default=b'submitted', max_length=255, choices=[(b'submitted', 'Submitted'), (b'running', 'Running'), (b'completed', 'Completed'), (b'deleted', 'Deleted')])),
                ('save_path', models.CharField(max_length=255, null=True, blank=True)),
                ('command', models.TextField()),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('modified_date', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Script',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('script_name', models.CharField(max_length=255)),
                ('slug', autoslug.fields.AutoSlugField(unique=True, editable=False)),
                ('script_description', models.TextField(null=True, blank=True)),
                ('script_order', models.PositiveSmallIntegerField(default=1)),
                ('is_active', models.BooleanField(default=True)),
                ('script_path', models.FileField(upload_to=b'')),
                ('execute_full_path', models.BooleanField(default=True)),
                ('save_path', models.CharField(help_text=b'By default save to the script name, this will change the output folder.', max_length=255, null=True, blank=True)),
                ('script_version', models.PositiveSmallIntegerField(default=0)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('modified_date', models.DateTimeField(auto_now=True)),
            ],
            bases=(wooey.models.mixins.ModelDiffMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ScriptGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group_name', models.TextField()),
                ('slug', autoslug.fields.AutoSlugField(unique=True, editable=False)),
                ('group_description', models.TextField(null=True, blank=True)),
                ('group_order', models.SmallIntegerField(default=1)),
                ('is_active', models.BooleanField(default=True)),
                ('user_groups', models.ManyToManyField(to='auth.Group', blank=True)),
            ],
            bases=(wooey.models.mixins.UpdateScriptsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ScriptParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('short_param', models.CharField(max_length=255)),
                ('script_param', models.CharField(max_length=255)),
                ('slug', autoslug.fields.AutoSlugField(unique=True, editable=False)),
                ('is_output', models.BooleanField(default=None)),
                ('required', models.BooleanField(default=False)),
                ('output_path', models.FilePathField(path=b'', max_length=255, allow_files=False, recursive=True, allow_folders=True)),
                ('choices', models.CharField(max_length=255, null=True, blank=True)),
                ('choice_limit', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('form_field', models.CharField(max_length=255)),
                ('default', models.CharField(max_length=255, null=True, blank=True)),
                ('input_type', models.CharField(max_length=255)),
                ('param_help', models.TextField(null=True, verbose_name=b'help', blank=True)),
                ('is_checked', models.BooleanField(default=False)),
            ],
            bases=(wooey.models.mixins.UpdateScriptsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ScriptParameterGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group_name', models.TextField()),
                ('script', models.ForeignKey(to='wooey.Script')),
            ],
            bases=(wooey.models.mixins.UpdateScriptsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ScriptParameters',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('_value', models.TextField(db_column='value')),
                ('job', models.ForeignKey(to='wooey.WooeyJob')),
                ('parameter', models.ForeignKey(to='wooey.ScriptParameter')),
            ],
        ),
        migrations.AddField(
            model_name='scriptparameter',
            name='parameter_group',
            field=models.ForeignKey(to='wooey.ScriptParameterGroup'),
        ),
        migrations.AddField(
            model_name='scriptparameter',
            name='script',
            field=models.ForeignKey(to='wooey.Script'),
        ),
        migrations.AddField(
            model_name='script',
            name='script_group',
            field=models.ForeignKey(to='wooey.ScriptGroup'),
        ),
        migrations.AddField(
            model_name='script',
            name='user_groups',
            field=models.ManyToManyField(to='auth.Group', blank=True),
        ),
        migrations.AddField(
            model_name='wooeyjob',
            name='script',
            field=models.ForeignKey(to='wooey.Script'),
        ),
        migrations.AddField(
            model_name='wooeyjob',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='wooeyfile',
            name='job',
            field=models.ForeignKey(to='wooey.WooeyJob'),
        ),
        migrations.AddField(
            model_name='wooeyfile',
            name='parameter',
            field=models.ForeignKey(blank=True, to='wooey.ScriptParameters', null=True),
        ),
    ]
