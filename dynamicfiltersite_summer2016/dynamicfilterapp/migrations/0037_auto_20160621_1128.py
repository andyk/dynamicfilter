# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-21 18:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0036_remove_ip_pair_pastworkers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='predicate',
            name='num_tickets',
            field=models.IntegerField(default=5),
        ),
    ]