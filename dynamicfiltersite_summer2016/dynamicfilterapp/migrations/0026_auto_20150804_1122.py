# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamicfilterapp', '0025_auto_20150722_1343'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='restaurant',
            name='text',
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='predicate0Status',
            field=models.IntegerField(default=5),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='predicate1Status',
            field=models.IntegerField(default=5),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='predicate2Status',
            field=models.IntegerField(default=5),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='predicate3Status',
            field=models.IntegerField(default=5),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='predicate4Status',
            field=models.IntegerField(default=5),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='predicate5Status',
            field=models.IntegerField(default=5),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='predicate6Status',
            field=models.IntegerField(default=5),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='predicate7Status',
            field=models.IntegerField(default=5),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='predicate8Status',
            field=models.IntegerField(default=5),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='predicate9Status',
            field=models.IntegerField(default=5),
        ),
    ]
