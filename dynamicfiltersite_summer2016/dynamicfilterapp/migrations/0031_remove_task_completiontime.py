# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-15 16:50
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0030_task_completiontime'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='completionTime',
        ),
    ]
