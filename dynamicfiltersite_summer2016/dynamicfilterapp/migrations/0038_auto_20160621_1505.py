# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-21 22:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0037_auto_20160621_1128'),
    ]

    operations = [
        migrations.AddField(
            model_name='ip_pair',
            name='num_no',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='ip_pair',
            name='num_yes',
            field=models.IntegerField(default=0),
        ),
    ]
