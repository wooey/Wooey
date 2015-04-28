# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AddScript',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('script_path', models.FileField(help_text='The file to Djanguify', upload_to=b'')),
            ],
        ),
        migrations.CreateModel(
            name='DjanguiJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('celery_id', models.CharField(max_length=255, null=True)),
                ('job_name', models.CharField(max_length=255)),
                ('job_description', models.TextField(null=True, blank=True)),
                ('script_command', models.TextField(null=True, blank=True)),
                ('celery_state', models.CharField(max_length=255, null=True, blank=True)),
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
                ('job_name', models.CharField(max_length=255)),
                ('job_description', models.TextField(null=True, blank=True)),
                ('command', models.TextField(null=True, blank=True)),
                ('celery_id', models.CharField(max_length=255, null=True, blank=True)),
                ('celery_state', models.CharField(max_length=255, null=True, blank=True)),
                ('save_path', models.CharField(max_length=255, null=True, blank=True)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('modified_date', models.DateTimeField(auto_now=True)),
                ('script_name', models.CharField(max_length=255)),
                ('slug', autoslug.fields.AutoSlugField(editable=False)),
                ('script_description', models.TextField(null=True, blank=True)),
                ('script_order', models.PositiveSmallIntegerField(default=1)),
                ('script_active', models.BooleanField(default=True)),
                ('script_path', models.CharField(max_length=255)),
                ('execute_full_path', models.BooleanField(default=True)),
                ('script_version', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ScriptGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group_name', models.TextField()),
                ('group_description', models.TextField(null=True, blank=True)),
                ('slug', autoslug.fields.AutoSlugField(editable=False)),
            ],
        ),
        migrations.CreateModel(
            name='ScriptParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('short_param', models.CharField(max_length=255)),
                ('script_param', models.CharField(max_length=255)),
                ('slug', autoslug.fields.AutoSlugField(editable=False)),
                ('is_output', models.BooleanField(default=None)),
                ('required', models.BooleanField(default=False)),
                ('output_path', models.FilePathField(path=b'/home/chris/Devel/djangui/testpp/testpp/user_uploads', max_length=255, allow_files=False, recursive=True, allow_folders=True)),
                ('choices', models.CharField(max_length=255, null=True, blank=True)),
                ('choice_limit', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('form_field', models.CharField(max_length=255)),
                ('default', models.CharField(max_length=255, null=True, blank=True)),
                ('input_type', models.CharField(max_length=255)),
                ('param_help', models.TextField(verbose_name=b'help')),
                ('is_checked', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='ScriptParameterGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group_name', models.TextField()),
                ('script', models.ForeignKey(to='djangui.Script')),
            ],
        ),
        migrations.CreateModel(
            name='ScriptParameters',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.TextField()),
                ('job', models.ForeignKey(to='djangui.DjanguiJob')),
                ('parameter', models.ForeignKey(to='djangui.ScriptParameter')),
            ],
        ),
        migrations.AddField(
            model_name='scriptparameter',
            name='parameter_group',
            field=models.ForeignKey(to='djangui.ScriptParameterGroup'),
        ),
        migrations.AddField(
            model_name='scriptparameter',
            name='script',
            field=models.ForeignKey(to='djangui.Script'),
        ),
        migrations.AddField(
            model_name='script',
            name='script_group',
            field=models.ForeignKey(to='djangui.ScriptGroup'),
        ),
        migrations.AddField(
            model_name='script',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='djanguijob',
            name='script',
            field=models.ForeignKey(to='djangui.Script'),
        ),
        migrations.AddField(
            model_name='djanguijob',
            name='user',
            field=models.OneToOneField(null=True, blank=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='addscript',
            name='script_group',
            field=models.ForeignKey(to='djangui.ScriptGroup'),
        ),
    ]
