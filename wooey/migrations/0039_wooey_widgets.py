# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-03-05 16:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("wooey", "0038_wooeyjob-choices"),
    ]

    operations = [
        migrations.CreateModel(
            name="WooeyWidget",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50, verbose_name="Widget Name")),
                (
                    "input_attributes",
                    models.TextField(
                        blank=True,
                        help_text='Extra attributes to the input field. The extra attributes MUST be specified like key="value".',
                        null=True,
                        verbose_name="Input Widget Extra Attributes",
                    ),
                ),
                (
                    "input_class",
                    models.CharField(
                        blank=True,
                        help_text="The class name(s) for the input field.",
                        max_length=255,
                        null=True,
                        verbose_name="Input Widget Class name(s)",
                    ),
                ),
                (
                    "input_properties",
                    models.CharField(
                        blank=True,
                        help_text="Additional properties to append to the input field.",
                        max_length=255,
                        null=True,
                        verbose_name="Input Widget Extra Properties",
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="scriptparameter",
            name="param_order",
            field=models.SmallIntegerField(
                default=0, help_text="The order the parameter appears to the user."
            ),
        ),
        migrations.AddField(
            model_name="scriptparameter",
            name="custom_widget",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="wooey.WooeyWidget",
            ),
        ),
    ]
